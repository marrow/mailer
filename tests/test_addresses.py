# encoding: utf-8
"""Test the TurboMail Message class."""

from __future__ import unicode_literals

from nose.tools import raises, eq_, assert_raises

from marrow.mailer.address import Address, AddressList, AutoConverter
from marrow.util.compat import unicode


class TestAddress(object):
    def test_punycode(self):
        addr = Address('Foo', 'foo@exámple.test')
        eq_(b'Foo <foo@xn--exmple-qta.test>', bytes(addr))
    
    def test_bytestring(self):
        addr = Address('Foo <foo@exámple.test>'.encode('utf-8'))
        eq_(b'Foo <foo@xn--exmple-qta.test>', bytes(addr))
    
    def test_address_from_addresslist(self):
        email = 'foo@example.com'
        addr = Address(AddressList([Address(email)]))
        eq_(email, unicode(addr))
    
    @raises(ValueError)
    def test_address_from_addresslist_limit_0(self):
        email = 'foo@example.com'
        addr = Address(AddressList())
    
    @raises(ValueError)
    def test_address_from_addresslist_limit_2(self):
        email = 'foo@example.com'
        addr = Address(AddressList([Address(email), Address(email)]))
    
    def test_initialization_with_tuple(self):
        name = 'Foo'
        emailaddress = 'foo@example.com'
        address = Address((name, emailaddress))
        eq_('%s <%s>' % (name, emailaddress), unicode(address))
    
    def test_initialization_with_string(self):
        emailaddress = 'foo@example.com'
        address = Address(emailaddress)
        eq_(emailaddress, unicode(address))
    
    def test_initialization_with_named_string(self):
        emailaddress = 'My Name <foo@example.com>'
        address = Address(emailaddress)
        eq_(emailaddress, unicode(address))
    
    @raises(TypeError)
    def test_invalid_initialization(self):
        Address(123)
    
    def test_compare_address(self):
        addr1 = Address('foo@example.com')
        addr2 = Address(' foo@example.com  ')
        eq_(addr1, addr2)
    
    def test_compare_unicode(self):
        addr = Address('foo@example.com')
        eq_(addr, 'foo@example.com')
    
    def test_compare_bytestring(self):
        addr = Address('foo@example.com')
        eq_(addr, b'foo@example.com')
    
    def test_compare_tuple(self):
        addr = Address('foo', 'foo@example.com')
        eq_(addr, ('foo', 'foo@example.com'))
    
    @raises(NotImplementedError)
    def test_compare_othertype(self):
        addr = Address('foo@example.com')
        addr != 123
    
    def test_len(self):
        addr = Address('foo@example.com')
        eq_(len(addr), len('foo@example.com'))
    
    def test_repr(self):
        addr = Address('foo@example.com')
        eq_(repr(addr), 'Address("foo@example.com")')
    
    def test_validation_truncates_at_second_at_character(self):
        # This is basically due to Python's parseaddr behavior.
        eq_('bad@user', Address('bad@user@example.com'))
    
    @raises(ValueError)
    def test_validation_rejects_addresses_without_at(self):
        # TODO: This may be actually a valid input - some mail systems allow to
        # use only the local part which will be qualified by the MTA
        Address('baduser.example.com')
    
    def test_validation_accepts_uncommon_local_parts(self):
        Address('good-u+s+er@example.com')
        # This address caused 100% CPU load for 50s in Python's (2.5.2) re 
        # module on Fedora Linux 10 (AMD x2 4200).
        Address('steve.blackmill.rules.for.all@bar.blackmill-goldworks.example')
        Address('customer/department=shipping@example.com')
        Address('$A12345@example.com ')
        Address('!def!xyz%abc@example.com ')
        Address('_somename@example.com')
        Address('!$&*-=^`|~#%\'+/?_{}@example.com')
    
    def test_revalidation(self):
        addr = Address('_somename@example.com')
        eq_(addr.valid, True)
    
# TODO: Later
#    def test_validation_accepts_quoted_local_parts(self):
#        Address('"Fred Bloggs"@example.com ')
#        Address('"Joe\\Blow"@example.com ')
#        Address('"Abc@def"@example.com ')
#        Address('"Abc\@def"@example.com')
    
    def test_validation_accepts_multilevel_domains(self):
        Address('foo@my.my.company-name.com')
        Address('blah@foo-bar.example.com')
        Address('blah@duckburg.foo-bar.example.com')
    
    def test_validation_accepts_domain_without_tld(self):
        eq_('user@company', Address('user@company'))
    
    def test_validation_rejects_local_parts_starting_or_ending_with_dot(self):
        assert_raises(ValueError, Address, '.foo@example.com')
        assert_raises(ValueError, Address, 'foo.@example.com')
    
    def test_validation_rejects_double_dot(self):
        assert_raises(ValueError, Address, 'foo..bar@example.com')

# TODO: Later
#    def test_validation_rejects_special_characters_if_not_quoted(self):
#        for char in '()[]\;:,<>':
#            localpart = 'foo%sbar' % char
#            self.assertRaises(ValueError, Address, '%s@example.com' % localpart)
#            Address("%s"@example.com' % localpart)

# TODO: Later
#    def test_validation_accepts_ip_address_literals(self):
#        Address('jsmith@[192.168.2.1]')


class TestAddressList(object):
    """Test the AddressList helper class."""
    
    addresses = AutoConverter(AddressList)
    
    def setUp(self):
        self.addresses = AddressList()
    
    def tearDown(self):
        del self.addresses
    
    def test_assignment(self):
        eq_([], self.addresses)
    
    def test_assign_single_address(self):
        address = 'user@example.com'
        self.addresses = address
        
        eq_(self.addresses, [address])
        eq_(unicode(self.addresses), address)
    
    def test_assign_list_of_addresses(self):
        addresses = ['user1@example.com', 'user2@example.com']
        self.addresses = addresses
        eq_(', '.join(addresses), unicode(self.addresses))
        eq_(addresses, self.addresses)
    
    def test_assign_list_of_named_addresses(self):
        addresses = [('Test User 1', 'user1@example.com'), ('Test User 2', 'user2@example.com')]
        self.addresses = addresses
        
        string_addresses = [unicode(Address(*value)) for value in addresses]
        eq_(', '.join(string_addresses), unicode(self.addresses))
        eq_(string_addresses, self.addresses)
    
    def test_assign_item(self):
        self.addresses.append('user1@example.com')
        eq_(self.addresses[0], 'user1@example.com')
        self.addresses[0] = 'user2@example.com'
        
        assert isinstance(self.addresses[0], Address)
        eq_(self.addresses[0], 'user2@example.com')
    
    def test_assign_slice(self):
        self.addresses[:] = ('user1@example.com', 'user2@example.com')
        
        assert isinstance(self.addresses[0], Address)
        assert isinstance(self.addresses[1], Address)
    
    def test_init_accepts_string_list(self):
        addresses = 'user1@example.com, user2@example.com'
        self.addresses = addresses
        
        eq_(addresses, unicode(self.addresses))
    
    def test_init_accepts_tuple(self):
        addresses = AddressList(('foo', 'foo@example.com'))
        eq_([('foo', 'foo@example.com')], addresses)
    
    def test_bytes(self):
        self.addresses = [('User1', 'foo@exámple.test'), ('User2', 'foo@exámple.test')]
        eq_(bytes(self.addresses), b'User1 <foo@xn--exmple-qta.test>, User2 <foo@xn--exmple-qta.test>')
    
    def test_repr(self):
        eq_(repr(self.addresses), 'AddressList()')
        
        self.addresses = ['user1@example.com', 'user2@example.com']
        
        eq_(repr(self.addresses),
            'AddressList("user1@example.com, user2@example.com")')
    
    @raises(ValueError)
    def test_invalid_init(self):
        AddressList(2)
    
    def test_addresses(self):
        self.addresses = [('Test User 1', 'user1@example.com'), ('Test User 2', 'user2@example.com')]
        eq_(self.addresses.addresses, AddressList('user1@example.com, user2@example.com'))
    
    def test_validation_strips_multiline_addresses(self):
        self.addresses = 'user.name+test@info.example.com'
        evil_lines = ['eviluser@example.com', 'To: spammeduser@example.com', 'From: spammeduser@example.com']
        evil_input = '\n'.join(evil_lines)
        self.addresses.append(evil_input)
        eq_(['user.name+test@info.example.com', evil_lines[0]], self.addresses)
    
    def test_return_addresses_as_strings(self):
        self.addresses = 'foo@exámple.test'
        encoded_address = b'foo@xn--exmple-qta.test'
        eq_([encoded_address], self.addresses.string_addresses)
