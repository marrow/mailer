# encoding: utf-8

import mailbox


__all__ = ['MaildirTransport']

log = __import__('logging').getLogger(__name__)



class MaildirTransport(object):
    """A modern UNIX maildir on-disk file delivery transport."""
    
    __slots__ = ('ephemeral', 'box', 'directory', 'folder', 'create', 'separator')
    
    def __init__(self, config):
        self.box = None
        self.directory = config.get('directory', None) # maildir directory
        self.folder = config.get('folder', None) # maildir folder to deliver to
        self.create = config.get('create', False) # create folder if missing
        self.separator = config.get('separator', '!')
        
        if not self.directory:
            raise ValueError("You must specify the path to a maildir tree to write messages to.")
    
    def startup(self):
        self.box = mailbox.Maildir(self.directory)
        
        if self.folder:
            try:
                folder = self.box.get_folder(self.folder)
            
            except mailbox.NoSuchMailboxError:
                if not self.create: # pragma: no cover
                    raise # TODO: Raise appropraite internal exception.
                
                folder = self.box.add_folder(self.folder)
            
            self.box = folder
        
        self.box.colon = self.separator
    
    def deliver(self, message):
        # TODO: Create an ID based on process and thread IDs.
        # Current bhaviour may allow for name clashes in multi-threaded.
        self.box.add(mailbox.MaildirMessage(str(message)))
    
    def shutdown(self):
        self.box = None
