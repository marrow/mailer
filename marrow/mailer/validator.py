# encoding: utf-8
#
# This file was taken from webpyte (r179):
# http://code.google.com/p/webpyte/source/browse/trunk/webpyte/email_validator.py
# According to the docstring, it is licensed as 'public domain'
# 
# Modifications:
# * Wed Mar 25 2009 Felix Schwarz
# - Removed 'from __future__ import absolute_import to stay compatible with Python 2.3/2.4
# * Fri Mar 27 2009 Felix Schwarz
# - Disabled DNS server discovery on module import
# - added __all__ declaration
# - modified domain validator so that domains without second-level domain will
#   be accepted as well.
#

"""A method of validating e-mail addresses and mail domains.

This module aims to provide the ultimate functions for:
* domain validation, and
* e-mail validation.

Why not just use a regular expression?
======================================
http://haacked.com/archive/2007/08/21/i-knew-how-to-validate-an-email-address-until-i.aspx

There are many regular expressions out there for this. The "perfect one" is
several KB long and therefore unmaintainable (Perl people wrote it...).

This is 2009 and domain rules are changing too. Impossible domain names have
become possible, international domain names are real...

So validating an e-mail address is more complex than you might think. Take a
look at some of the rules:
http://en.wikipedia.org/wiki/E-mail_address#RFC_specification

How to do it then?
==================
I believe the solution should combine simple regular expressions with
imperative programming.

E-mail validation is also dependent on the robustness principle:
"Be conservative in what you do, be liberal in what you accept from others."
http://en.wikipedia.org/wiki/Postel%27s_law

This module recognizes that e-mail validation can be done in several different
ways, according to purpose:

1) Most of the time you just want validation according to the standard rules.
So just say:  v = EmailValidator()

2) If you are creating e-mail addresses for your server or your organization,
you might need to satisfy a stricter policy such as "dash is not allowed in
email addresses". The EmailValidator constructor accepts a *local_part_chars*
argument to help build the right regular expression for you.
Example:  v = EmailValidator(local_part_chars='.-+_')

3) What about typos? An erroneous dot at the end of a typed email is typical.
Other common errors with the dots revolve around the @: user@.domain.com.
These typing mistakes can be automatically corrected, saving you from doing
it manually. For this you use the *fix* flag when instantiating a validator:

    d = DomainValidator(fix=True)
    domain, error_message = d.validate('.supercalifragilistic.com.br')
    if error_message:
        print 'Invalid domain: ' + domain
    else:
        print 'Valid domain: ' + domain

4) TODO: Squash the bugs in this feature!
Paranoid people may wish to verify that the informed domain actually exists.
For that you can pass a *lookup_dns='a'* argument to the constructor, or even
*lookup_dns='mx'* to verify that the domain actually has e-mail servers.
To use this feature, you need to install the *pydns* library:

     easy_install -UZ pydns

How to use
==========

The validating methods return a tuple (email, error_msg).
*email* is the trimmed and perhaps fixed email.
*error_msg* is an empty string when the e-mail is valid.

Typical usage is:

    v = EmailValidator() # or EmailValidator(fix=True)
    email = raw_input('Type an email: ')
    email, err = v.validate(email)
    if err:
        print 'Error: ' + err
    else:
        print 'E-mail is valid: ' + email  # the email, corrected

There is also an EmailHarvester class to collect e-mail addresses from any text.

Authors: Nando Florestan, Marco Ferreira
Code written in 2009 and donated to the public domain.
"""

import re

__all__ = ['ValidationException', 'BaseValidator', 'DomainValidator', 'EmailValidator', 'EmailHarvester']


class ValidationException(ValueError):
    pass


class BaseValidator(object):
    def validate_or_raise(self, *a, **k):
        """Some people would condemn this whole module screaming:
        "Don't return success codes, use exceptions!"
        This method allows them to be happy, too.
        """
        
        validate, err = self.validate(*a, **k)
        
        if err:
            raise ValidationException(err)
        
        return validate


class DomainValidator(BaseValidator):
    """A domain name validator that is ready for internationalized domains.
    
    http://en.wikipedia.org/wiki/Internationalized_domain_name
    http://en.wikipedia.org/wiki/Top-level_domain
    """
    # non_international_regex = re.compile(r"^[a-z0-9][a-z0-9\.\-]*\.[a-z]+$",
    #domain_pattern = r'[\w][\w\.\-]+?\.[\w]+'
    # fs: New domain regex that accepts domains without second-level domain also
    domain_pattern = r'[\w]+([\w\.\-]+\w)?'
    domain_regex = \
        re.compile('^' + domain_pattern + '$', re.IGNORECASE | re.UNICODE)

    # OpenDNS has a feature that bites us. If you are using OpenDNS, and you
    # type in your browser a domain that does not exist, OpenDNS catches that
    # and presents a page. "Did you mean www.hovercraft.eels?"
    # For us, this feature appears as a false positive when looking up the
    # DNS server. So we try to work around it:
    false_positive_ips = ['208.67.217.132']

    def __init__(self, fix=False, lookup_dns=None):
        self.fix = fix
        
        if lookup_dns:
            try:
                import DNS
            except ImportError: # pragma: no cover
                raise ImportError("To enable DNS lookup of domains install the PyDNS package.")
            
            lookup_dns = lookup_dns.lower()
            if lookup_dns not in ('a', 'mx'):
                raise RuntimeError("Not a valid *lookup_dns* value: " + lookup_dns)
        
        self._lookup_dns = lookup_dns

    def _apply_common_rules(self, part, maxlength):
        """This method contains the rules that must be applied to both the
        domain and the local part of the e-mail address.
        """
        part = part.strip()
        
        if self.fix:
            part = part.strip('.')
        
        if not part:
            return part, 'It cannot be empty.'
        
        if len(part) > maxlength:
            return part, 'It cannot be longer than %i chars.' % maxlength
        
        if part[0] == '.':
            return part, 'It cannot start with a dot.'
        
        if part[-1] == '.':
            return part, 'It cannot end with a dot.'
        
        if '..' in part:
            return part, 'It cannot contain consecutive dots.'
        
        return part, ''

    def validate_domain(self, part):
        part, err = self._apply_common_rules(part, maxlength=255)
        
        if err:
            return part, 'Invalid domain: %s' % err
        
        if not self.domain_regex.search(part):
            return part, 'Invalid domain.'
        
        if self._lookup_dns and not self.lookup_domain(part):
            return part, 'Domain does not seem to exist.'
        
        return part.lower(), ''

    validate = validate_domain

    # TODO: As an option, DNS lookup on the domain:
    # http://mail.python.org/pipermail/python-list/2008-July/497997.html

    def lookup_domain(self, domain, lookup_record=None, **kw):
        """Looks up the DNS record for *domain* and returns:
        
        * None if it does not exist,
        * The IP address if looking up the "A" record, or
        * The list of hosts in the "MX" record.
        
        The return value, if treated as a boolean, says whether a domain exists.
        
        You can pass "a" or "mx" as the *lookup_record* parameter. Otherwise,
        the *lookup_dns* parameter from the constructor is used.
        "a" means verify that the domain exists.
        "mx" means verify that the domain exists and specifies mail servers.
        """
        import DNS
        
        lookup_record = lookup_record.lower() if lookup_record else self._lookup_dns
        
        if lookup_record not in ('a', 'mx'):
            raise RuntimeError("Not a valid lookup_record value: " + lookup_record)
        
        if lookup_record == "a":
            request = DNS.Request(domain, **kw)
            
            try:
                answers = request.req().answers
            
            except (DNS.Lib.PackError, UnicodeError):
                # A part of the domain name is longer than 63.
                return False
            
            if not answers:
                return False
            
            result = answers[0]['data'] # This is an IP address
            
            if result in self.false_positive_ips: # pragma: no cover
                return False
            
            return result
        
        try:
            return DNS.mxlookup(domain)
        
        except UnicodeError:
            pass
        
        return False


class EmailValidator(DomainValidator):
    # TODO: Implement all rules!
    # http://tools.ietf.org/html/rfc3696
    # http://en.wikipedia.org/wiki/E-mail_address#RFC_specification
    # TODO: Local part in quotes?
    # TODO: Quoted-printable local part?

    def __init__(self, local_part_chars=".-+_!#$%&'/=`|~?^{}*", **k):
        super(EmailValidator, self).__init__(**k)
        # Add a backslash before the dash so it can go into the regex:
        self.local_part_pattern = '[a-z0-9' + local_part_chars.replace('-', r'\-') + ']+'
        # Regular expression for validation:
        self.local_part_regex = re.compile('^' + self.local_part_pattern + '$', re.IGNORECASE)

    def validate_local_part(self, part):
        part, err = self._apply_common_rules(part, maxlength=64)
        if err:
            return part, 'Invalid local part: %s' % err
        if not self.local_part_regex.search(part):
            return part, 'Invalid local part.'
        return part, ''
        # We don't go lowercase because the local part is case-sensitive.

    def validate_email(self, email):
        if not email:
            return email, 'The e-mail is empty.'
        
        parts = email.split('@')
        
        if len(parts) != 2:
            return email, 'An email address must contain a single @'
        
        local, domain = parts
        
        # Validate the domain
        domain, err = self.validate_domain(domain)
        if err:
            return email, "The e-mail has a problem to the right of the @: %s" % err
        
        # Validate the local part
        local, err = self.validate_local_part(local)
        if err:
            return email, "The email has a problem to the left of the @: %s" % err
        
        # It is valid
        return local + '@' + domain, ''

    validate = validate_email


class EmailHarvester(EmailValidator):
    def __init__(self, *a, **k):
        super(EmailHarvester, self).__init__(*a, **k)
        # Regular expression for harvesting:
        self.harvest_regex = \
            re.compile(self.local_part_pattern + '@' + self.domain_pattern,
                       re.IGNORECASE | re.UNICODE)

    def harvest(self, text):
        """Iterator that yields the e-mail addresses contained in *text*."""
        for match in self.harvest_regex.finditer(text):
            # TODO: optionally validate before yielding?
            # TODO: keep a list of harvested but not validated?
            yield match.group().replace('..', '.')


# rfc822_specials = '()<>@,;:\\"[]'

# is_address_valid(addr):
# # First we validate the name portion (name@domain)
# c = 0
# while c < len(addr):
#     if addr[c] == '"' and (not c or addr[c - 1] == '.' or addr[c - 1] == '"'):
#         c = c + 1
#         while c < len(addr):
#             if addr[c] == '"': break
#             if addr[c] == '\\' and addr[c + 1] == ' ':
#                 c = c + 2
#                 continue
#             if ord(addr[c]) < 32 or ord(addr[c]) >= 127: return 0
#             c = c + 1
#         else: return 0
#         if addr[c] == '@': break
#         if addr[c] != '.': return 0
#         c = c + 1
#         continue
#     if addr[c] == '@': break
#     if ord(addr[c]) <= 32 or ord(addr[c]) >= 127: return 0
#     if addr[c] in rfc822_specials: return 0
#     c = c + 1
# if not c or addr[c - 1] == '.': return 0
# 
# # Next we validate the domain portion (name@domain)
# domain = c = c + 1
# if domain >= len(addr): return 0
# count = 0
# while c < len(addr):
#     if addr[c] == '.':
#         if c == domain or addr[c - 1] == '.': return 0
#         count = count + 1
#     if ord(addr[c]) <= 32 or ord(addr[c]) >= 127: return 0
#     if addr[c] in rfc822_specials: return 0
#     c = c + 1
# 
# return count >= 1
