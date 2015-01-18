from logging import info
from webapp2 import RequestHandler, WSGIApplication
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.api import urlfetch

class DefaultHandler(RequestHandler):
    def get(self):
        info(self.request.path_info)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(self.request)
    post = get

class TestHandler(RequestHandler):
    def get(self):
        info(self.request)
        info(self.request.path_info)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('\n\n\n\n')
        self.response.write(self.request)
        from google.appengine.api import mail
        mail.send_mail(sender='admin@adeorz.appspotmail.com',
                       #to='adereg@163.com',
                       to='a@txtlxt.appspotmail.com',
                       subject='fetch',
                       body='hehe')
    post = get

class ReceiveMailHandler(InboundMailHandler):
    def receive(self, mail_message):
        info(self.request.path_info)
        fetch_kwargs = dict(url=mail_message.subject)
        contents, logs = self._fetch(fetch_kwargs)
        content = ''.join(contents)
        log = ''.join(str(l) + '\n' for l in logs)
        attachments = content and {'attachments':[('anonymous', content)]} or {}
        from google.appengine.api import mail
        mail.send_mail(sender='admin@adeorz.appspotmail.com',
                       to='adereg@163.com',
                       subject='fetch',
                       body=log,
                       **attachments
                       )
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(log)
    @staticmethod
    def _fetch(kwargs):
        contents, logs = [], []
        start, range_size = 0, 40*1024*1024  # 40MB
        for i in xrange(30):
            # Fetch request
            kwargs['deadline'] = 60
            headers = kwargs.setdefault('headers', {})
            headers['range'] = 'bytes=%d-%d' % (start, start+range_size-1)
            logs.append(kwargs)
            result = urlfetch.fetch(**kwargs)
            logs.append(result.headers)
            # Content
            if result.status_code in (200, 206):
                contents.append(result.content)
            else:
                logs.append('Error return code %d' % result.status_code)
                break
            # Next range
            if not result.content_was_truncated:
                break
            elif 'Range-Content' in result.headers:
                start += len(result.content)
            else:
                logs.append('Error: File truncated!')
                break
        else:
            logs.append('Error: File too big!')
        return contents, logs
    @staticmethod
    def _parse_payloads(mail_message):
        payloads = dict(body='')
        for part in mail_message.original.walk():
            if part.get('Content-Disposition'):
                payloads.setdefault('attachments', []).append(
                        (part.get_filename(), part.get_payload(decode=True)))
            elif part.get_content_type() == 'text/plain':
                payloads['body'] = part.get_payload(decode=True).decode(
                                   part.get_content_charset())
            elif part.get_content_type() == 'text/html':
                payloads['html'] = part.get_payload(decode=True).decode(
                                   part.get_content_charset())
        info(payloads)
        return payloads

app = WSGIApplication([
    ReceiveMailHandler.mapping(),
    (r'/1', TestHandler),
    (r'/.*', DefaultHandler),
], debug=True)
