# encoding: utf-8

import logging



class MailHandler(logging.Handler):
    """A class which sends records out via e-mail.
    
    This handler should be configured using the same configuration
    directives that TurboMail itself understands.  If you do not specify
    `mail.on` in the configuration, this handler will attempt to use
    the most recently configured TurboMail environment.
    
    Be sure that TurboMail is running before messages are emitted using
    this handler, and be careful how many notifications get sent.
    
    It is suggested to use background delivery using the 'demand' manager.
    
    Configuration options for this handler are as follows::
    
        * mail.handler.priorities = [True/False]
          Set message priority using the following formula:
            record.levelno / 10 - 3
        
        * 
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
        
        if config and 'mail.on' in config:
            # Initilize TurboMail using the configuration directives passed
            # to this handler, generally from an INI configuration file.
            turbomail.interface.start(config)
            return
        
        # If we get a configuration that doesn't explicitly start TurboMail
        # we use the configuration to populate the Message instance.
        self.config = config
    
    def emit(self, record):
        """Emit a record."""
        
        try:
            message = Message()
            
            if self.config:
                for i, j in self.config.iteritems():
                    if i.startswith('mail.message'):
                        i = i[13:]
                        setattr(message, i, j)
            
            message.plain = self.format(record)
            message.send()
        
        except (KeyboardInterrupt, SystemExit):
            raise
        
        except:
            self.handleError(record)


logging.MailHandler = MailHandler
