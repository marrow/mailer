# encoding: utf-8

import logging

from marrow.mailer import Mailer



class MailHandler(logging.Handler):
    """A class which sends records out via e-mail.
    
    This handler should be configured using the same configuration
    directives that Marrow Mailer itself understands.
    
    Be careful how many notifications get sent.
    
    It is suggested to use background delivery using the 'dynamic' manager.
    """
    
    def __init__(self, *args, **config):
        """Initialize the instance, optionally configuring TurboMail itself.
        
        If no additional arguments are supplied to the handler, re-use any
        existing running TurboMail configuration.
        
        To get around limitations of the INI parser, you can pass in a tuple
        of name, value pairs to populate the dictionary.  (Use `{}` dict
        notation in produciton, though.)
        """
        
        logging.Handler.__init__(self)
        
        self.config = dict()
        
        if args:
            config.update(dict(zip(*[iter(args)]*2)))
        
        self.mailer = Mailer(config).start()
        
        # If we get a configuration that doesn't explicitly start TurboMail
        # we use the configuration to populate the Message instance.
        self.config = config
    
    def emit(self, record):
        """Emit a record."""
        
        try:
            self.mailer.new(plain=self.format(record)).send()
        
        except (KeyboardInterrupt, SystemExit):
            raise
        
        except:
            self.handleError(record)


logging.MailHandler = MailHandler
