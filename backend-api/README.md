# 🌐 Infraestrutura de Redes com Mininet e Web API

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Mininet](https://img.shields.io/badge/Mininet-2.3-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791.svg)

Este repositório contém o projeto de infraestrutura de redes simulando o ambiente corporativo de uma empresa. A arquitetura foi construída utilizando **Mininet** para orquestração da topologia e integra uma aplicação **FastAPI** real comunicando-se com um banco de dados **PostgreSQL** através de nós virtuais.

## 🏗️ Arquitetura da Rede

A topologia foi desenhada com segregação rigorosa de serviços e clientes, implementando roteamento estático avançado e regras de firewall (iptables).

A rede é dividida nas seguintes sub-redes:
- **DMZ (172.27.0.0/12):** Contém o Cliente Externo (CE) e a interface externa do Firewall.
- **Clientes Internos (192.168.133.0/24):** Hosts `c1` a `c5`.
- **Serviços (192.168.13.0/24):** Hospeda os servidores FTP (`servico2`), NFS (`servico1`) e a **Web API** (`web_api`).
- **Banco de Dados (192.168.53.0/24):** Servidor PostgreSQL isolado.

O *core* da rede é interligado por roteadores virtuais (`r1`, `r2`, `r3`) distribuindo o tráfego de forma otimizada.

## 🛡️ Segurança e Firewall (iptables)

O nó `fw` (Firewall) atua como a porta de entrada da DMZ para as redes internas, operando com uma política rigorosa de **Default Deny**. As regras de `iptables` garantem que o tráfego externo só alcance serviços autorizados:
- ✅ **Permitido:** Tráfego TCP para a porta `8000` (Web API).
- ✅ **Permitido:** Tráfego TCP para a porta `21` (FTP).
- ✅ **Permitido:** Tráfego TCP para a porta `2049` (NFS).
- ❌ **Bloqueado:** ICMP (Ping) do meio externo para a rede interna.
- ❌ **Bloqueado:** Qualquer outro tráfego não explicitamente liberado.

## 🚀 Tecnologias Utilizadas
- **Infraestrutura e Redes:** Mininet, Open vSwitch, iptables, Roteamento Estático Linux (`ip route`).
- **Backend:** FastAPI, Uvicorn, SQLAlchemy.
- **Banco de Dados:** PostgreSQL, psycopg2.

## ⚙️ Como Executar o Projeto

### Pré-requisitos
Ambiente Linux (Ubuntu recomendado) com Mininet e Python 3 instalados.

```bash
sudo apt update
sudo apt install mininet openvswitch-testcontroller python3-pip python3-venv -y
sudo ln -s /usr/bin/ovs-testcontroller /usr/bin/controller
