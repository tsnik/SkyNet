from OpenSSL import crypto, SSL
from socket import gethostname
from twisted.internet import ssl,reactor
from twisted.application import internet
from pprint import pprint
from time import gmtime, mktime
from os.path import exists, join
from os import mkdir


def create_self_signed_cert(cert_dir, app_name):
    """
    If datacard.crt and datacard.key don't exist in cert_dir, create a new
    self-signed cert and keypair and write them into that directory.
    """
    CERT_FILE = app_name + ".crt"
    KEY_FILE = app_name + ".key"
    if not exists(cert_dir):
        mkdir(cert_dir)
    if not exists(join(cert_dir, CERT_FILE)) \
            or not exists(join(cert_dir, KEY_FILE)):

        # create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)

        # create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "RU"
        cert.get_subject().L = "Moscow"
        cert.get_subject().OU = app_name
        cert.get_subject().CN = gethostname()
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha1')

        open(join(cert_dir, CERT_FILE), "wt").write(
            crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("UTF-8"))
        open(join(cert_dir, KEY_FILE), "wt").write(
            crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("UTF-8"))


class CertManager:
    def __init__(self, key_folder, peers_subfolder, name):
        self.name = name
        self.key_folder = key_folder
        self.peers_subfolder = peers_subfolder

    def create_server(self, port, factory, iface):
        sslcontext = ssl.DefaultOpenSSLContextFactory(self.key_folder + '/' + self.name + '.key',
                                                      self.key_folder + '/' + self.name + '.crt')
        return internet.SSLServer(port, factory, sslcontext, interface=iface)

    def connect_to_server(self, ip, port, factory):
        sslcontext = ssl.DefaultOpenSSLContextFactory(self.key_folder + '/' + self.name + '.key',
                                                      self.key_folder + '/' + self.name + '.crt')
        reactor.connectSSL(ip, port, factory, sslcontext)

    def save_client_cert(self, ip):
        pass
