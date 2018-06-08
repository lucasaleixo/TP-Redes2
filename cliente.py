# ========================================================================
 # Projeto destinado a disciplina de Redes de Computadores II
 # Autores: Lucas Aleixo de Paula e Lucas Olini
 # Entrega: 08/06/2018
 # ======================================================================== 

import socket
import struct
import sys
import pickle

# Endereco e porta para recebimento
ADDRESS = '224.1.1.1'
PORTA_MULTICAST = 3333

# Definicao da porta para resposta
PORTA_RESPOSTA = 4321

# Definicao do objeto Mensagem
class Mensagem(object):
    tipo = None # 1 - Pegar id inicial; 2 - Resposta id inicial; 3 - Pedido Heartbeat; 4 - Resposta Hearbeat ; 5 - Calculo;  6 - Reposta Calculo
    id_servidor = None
    numero_1 = None
    numero_2 = None
    operacao = ""
    resultado = ""

    # Inicializa os atributos da Mensagem
    def __init__(self, tipo, id_servidor=None, numero_1=None, numero_2=None, operacao=None, resultado=None):
        self.tipo = tipo
        self.id_servidor = id_servidor
        self.numero_1 = numero_1
        self.numero_2 = numero_2
        self.operacao = operacao
        self.resultado = resultado

# Funcao main
if __name__ == '__main__':
    # Abre o arquivo log_cliente.txt em modo de escrita e printa o cabecalho
    log = open("log_cliente.txt","a")
    log.write("\n# ==========================================================")
    log.write("\n# Projeto destinado a disciplina de Redes de Computadores II")
    log.write("\n# Autores: Lucas Aleixo de Paula e Lucas Olini")
    log.write("\n# Entrega: 08/06/2018")
    log.write("\n# ==========================================================\n")

    # Recebe o endereco, porta, operacao e operandos como parametro
    try:
        numero_1 = float(sys.argv[1])
        operacao = sys.argv[2]
        numero_2 = float(sys.argv[3])

	# Insere os dados no log de execucao do cliente
	log.write("Endereco IP (TRANSMISSAO): %s\n" % str(ADDRESS))
	log.write("Endereco IP (CLIENTE): %s\n" % socket.gethostbyname(socket.gethostname()))
        log.write("Operador 1: %s\n" % str(numero_1))
	log.write("Operacao: %s\n" % str(operacao))
	log.write("Operador 2: %s\n" % (numero_2))

    # Se os parametros estiverem incompletos, emite mensagem de erro
    except IndexError:
        print 'Entrada: %s OP1 OPERACAO OP2' % sys.argv[0]
        sys.exit(1)

    # Define o socket de recebimento, e conecta de acordo com a porta passada como parametro
    socket_recebimento = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    socket_recebimento.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    log.write("\nEstabeleceu o socket para recebimento\n")
    socket_recebimento.bind(('', PORTA_RESPOSTA))

    # Define o socket de envio
    socket_envio = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    socket_envio.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 10)
    log.write("\nEstabeleceu o socket para envio\n")

    # Transmite os dados para o grupo MULTICAST
    print >>sys.stderr, 'Enviando "%s"' % operacao
    mensagem = Mensagem(5, None, numero_1, numero_2, operacao, None)
    mensagem_serializada = pickle.dumps(mensagem, 2)
    socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
    log.write("\nEnviando: %s\nPara: %s\nPorta: %d\n" % (str(numero_1) + operacao + str(numero_2),ADDRESS,PORTA_MULTICAST))

    # Define o tempo de TIMEOUT para o socket de recebimento
    log.write("\nDefiniu o timeout para a comunicacao\n")
    socket_recebimento.settimeout(2)

    # Procura por respostas de todos os servidores
    while True:
        print >>sys.stderr, '\nAguardando para receber'
        log.write("\nAguardando para receber\n")

        try:
            # Recebe os dados do servidor que respondeu
            data, server = socket_recebimento.recvfrom(1024)
	    log.write("\nRecebeu o resultado da operacao\n")
            mensagem = pickle.loads(data)

            log.write("\nResultado: %s\nServidor que respondeu: %s\n" % (mensagem.resultado, mensagem.id_servidor))
            print >>sys.stderr, '\nRecebeu: %s\nDe: %s\n' % (mensagem.resultado, mensagem.id_servidor)
            break

        except socket.timeout:
            # Se der timeout, encerra a execucao do cliente
            print >>sys.stderr, 'timed out, no more responses'
            socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
            log.write("TIMEOUT\n")

        else:
            # Se receber os dados com sucesso, printa para o usuario
            print >>sys.stderr, 'Recebeu "%s" de %s' % (mensagem.resultado, server)

    #
    #finally:
    #    # Ao final da execucao, fecha o socket e o arquivo de log
    #    print >>sys.stderr, 'closing socket'
    #    log.write("Fechando o socket\n")
    #    log.close()
    #    socket_envio.close()
    #    socket_recebimento.close()
