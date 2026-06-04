from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.cli import CLI
from mininet.log import setLogLevel

class LinuxRouter(Node):
    """Ativa o roteamento (ip_forward) nos nós que serão Roteadores/Firewall"""
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

class MyTopo(Topo):
    def build(self):
        # 1. CRIANDO OS SWITCHES
        sdmz = self.addSwitch('sdmz')
        s1 = self.addSwitch('s1')  # Clientes Internos
        s2 = self.addSwitch('s2')  # Serviços
        s3 = self.addSwitch('s3')  # Data Bases

        # 2. CRIANDO O FIREWALL E ROTEADORES
        fw = self.addNode('fw', cls=LinuxRouter, ip='172.27.0.254/12')
        r1 = self.addNode('r1', cls=LinuxRouter, ip='192.168.133.254/24')
        r2 = self.addNode('r2', cls=LinuxRouter, ip='192.168.13.254/24')
        r3 = self.addNode('r3', cls=LinuxRouter, ip='192.168.53.254/24')

        # 3. CRIANDO OS HOSTS (COM SEUS IPs PADRÕES)
        ce = self.addHost('ce', ip='172.27.0.1/12', defaultRoute='via 172.27.0.254')

        # Rede Clientes Internos (Sub-rede 1)
        c1 = self.addHost('c1', ip='192.168.133.1/24', defaultRoute='via 192.168.133.254')
        c2 = self.addHost('c2', ip='192.168.133.2/24', defaultRoute='via 192.168.133.254')
        c3 = self.addHost('c3', ip='192.168.133.3/24', defaultRoute='via 192.168.133.254')
        c4 = self.addHost('c4', ip='192.168.133.4/24', defaultRoute='via 192.168.133.254')
        c5 = self.addHost('c5', ip='192.168.133.5/24', defaultRoute='via 192.168.133.254')

        # Rede de Serviços (Sub-rede 2)
        serv1 = self.addHost('servico1', ip='192.168.13.1/24', defaultRoute='via 192.168.13.254')
        serv2 = self.addHost('servico2', ip='192.168.13.2/24', defaultRoute='via 192.168.13.254')
        web_api = self.addHost('web_api', ip='192.168.13.3/24', defaultRoute='via 192.168.13.254')

        # Rede Data Bases (Sub-rede 3)
        db = self.addHost('db', ip='192.168.53.1/24', defaultRoute='via 192.168.53.254')

        # 4. CONECTANDO OS CABOS (LINKS) E CONFIGURANDO IPs DE INTERFACE
        # DMZ e Firewall
        self.addLink(ce, sdmz)
        self.addLink(fw, sdmz, intfName1='fw-eth0', params1={'ip': '172.27.0.254/12'})
        # Conectando FW ao Switch da rede Clientes Internos (conforme requisito 3 do projeto)
        self.addLink(fw, s1, intfName1='fw-eth1', params1={'ip': '192.168.133.253/24'})

        # Hosts <-> Switches
        for host in [c1, c2, c3, c4, c5]: self.addLink(host, s1)
        for host in [serv1, serv2, web_api]: self.addLink(host, s2)
        self.addLink(db, s3)

        # Roteadores <-> Switches
        self.addLink(r1, s1, intfName1='r1-eth0')
        self.addLink(r2, s2, intfName1='r2-eth0')
        self.addLink(r3, s3, intfName1='r3-eth0')

        # Roteadores interligados (Core da Rede) - Distribuindo os IPs do Indivíduo-9
        self.addLink(r1, r2, intfName1='r1-eth1', params1={'ip': '10.3.0.1/16'}, intfName2='r2-eth1', params2={'ip': '10.3.0.2/16'})
        self.addLink(r1, r3, intfName1='r1-eth2', params1={'ip': '10.8.0.1/16'}, intfName2='r3-eth1', params2={'ip': '10.8.0.2/16'})
        self.addLink(r2, r3, intfName1='r2-eth2', params1={'ip': '10.10.0.1/16'}, intfName2='r3-eth2', params2={'ip': '10.10.0.2/16'})

# ==========================================
# EXECUÇÃO DA REDE
# ==========================================
if __name__ == '__main__':
    setLogLevel('info')
    topo = MyTopo()
    net = Mininet(topo=topo)
    net.start()
    CLI(net)
    net.stop()