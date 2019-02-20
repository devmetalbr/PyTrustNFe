# -*- coding: utf-8 -*-
# © 10ADev - 2018
# # # Rafael Lima <rafael@10adev.com.br>
# # # Diogo Matos <diogo@10adev.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

"""
python -mzeep 'http://186.233.223.100:8080/tbw/services/WSEntrada?wsdl'
Operations:
     consultarAtividades(cpfUsuario: xsd:string, hashSenha: xsd:string, inscricaoMunicipal: xsd:string, codigoMunicipio: xsd:int) -> return: xsd:string
     nfdEntrada(cpfUsuario: xsd:string, hashSenha: xsd:string, codigoMunicipio: xsd:int, nfd: xsd:string) -> return: xsd:string
     nfdEntradaCancelar(cpfUsuario: xsd:string, hashSenha: xsd:string, nfd: xsd:string) -> return: xsd:


python -m zeep 'http://186.233.223.100:8080/tbw/services/WSSaida?wsdl'
Operations:
     nfdSaida(cpfUsuario: xsd:string, hashSenha: xsd:string, inscricaoMunicipal: xsd:string, recibo: xs


python -m zeep 'http://186.233.223.100:8080/tbw/services/WSUtil?wsdl'
Operations:
    urlNfd(codigoMunicipio: xsd:int, numeroNfd: xsd:int, serieNfd: xsd:int, inscricaoMunicipal: xsd:st
"""

import os
from requests import Session
from zeep import Client, settings
from zeep.transports import Transport
from requests.packages.urllib3 import disable_warnings
from lxml import etree
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfe.assinatura import Assinatura


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), 'templates')
    xml_send = render_xml(path, '%s.xml' % method, True, **kwargs)

    signer = Assinatura(certificado.pfx, certificado.password)
    xml_send = signer.assina_xml(xml_send, '')
    return xml_send


def _validate(method, xml):
    path = os.path.join(os.path.dirname(__file__), 'templates')
    schema = os.path.join(path, '%s.xsd' % method)

    nfe = etree.fromstring(xml)
    esquema = etree.XMLSchema(etree.parse(schema))
    esquema.validate(nfe)
    erros = [x.message for x in esquema.error_log]
    return erros


def _send(method, **kwargs):
    base_url = ''
    if method == 'urlNfd':
        base_url = 'http://186.233.223.100:8080/tbw/services/WSUtil?wsdl'
    elif method == 'nfdSaida':
        base_url = 'http://186.233.223.100:8080/tbw/services/WSSaida?wsdl'
    elif method in ['consultarAtividades', 'nfdEntrada']:
        base_url = 'http://186.233.223.100:8080/tbw/services/WSEntrada?wsdl'

    disable_warnings()
    session = Session()
    session.verify = False
    transport = Transport(session=session)
    client = Client(base_url, transport=transport)

    # header = '<?xml version="1.0" encoding="UTF-8" ?>'
    xml_send = kwargs['xml']
    # xml_send = header + kwargs['xml']
    response = client.service[method](
        cpfUsuario=kwargs.get('cpf_usuario', '55555555555'),
        hashSenha=kwargs.get('hash_senha', 'cRDtpNCeBiql5KOQsKVyrA0sAiA='),
        codigoMunicipio=kwargs.get('codigo_municipio', '3'),
        nfd=xml_send
    )

    try:
        response, obj = sanitize_response(response)
        return {
            'received_xml': str(response),
            'object': obj,
            'sent_xml': xml_send,
        }
    except Exception as e:
        return dict(erro=response)


def consultar_atividades(certificado, **kwargs):
    return _send(certificado, 'consultarAtividades', **kwargs)


def xml_nfd_entrada(certificado, **kwargs):
    return _render(certificado, 'nfdEntrada', **kwargs)


def nfd_entrada(**kwargs):
    """
    Envio de um xml com a solicitação de Emissão de Nota Fiscal Eletronica
    :param certificado:
    :param kwargs:
    :return:
    """
    return _send('nfdEntrada', **kwargs)


def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, 'RecepcionarLoteRpsV3', **kwargs)


def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs['xml'] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, 'RecepcionarLoteRpsV3', **kwargs)


if __name__ == '__main__':
    # TESTES:
    from pytrustnfe.certificado import Certificado

    certfile = open('/mnt/data/projects/outtech/nfse-itaqua/eurolls/certs/13680713_out.pfx', 'rb').read()
    certificado = Certificado(certfile, 'rpasco365')
    xmlfile = open(
        '/mnt/data/projects/outtech/nfse-itaqua/requirements/PyTrustNFe/pytrustnfe/nfse/itaqua/templates/nfdEntrada2.xml',
        'r'
    ).read()
    params = {
        'cpfUsuario': '55555555555',
        'hashSenha': 'cRDtpNCeBiql5KOQsKVyrA0sAiA=',
        'codigoMunicipio': 3,
        'xml': xmlfile,
    }

    params = {
        'cpfUsuario': '55555555555',
        'hashSenha': 'cRDtpNCeBiql5KOQsKVyrA0sAiA=',
        'codigoMunicipio': 3,
        'xml': xmlfile,
        'inscricaoMunicipal': '88133269',
        'ambiente': 'homologacao'
    }
    n = nfd_entrada(certificado)
    print(n)

    def test_render():
        return _render(certificado, 'nfdEntrada')

    # print(test_render())