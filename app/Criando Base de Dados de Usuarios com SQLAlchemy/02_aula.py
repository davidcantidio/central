

class Veiculo:

    rodas = None

    def __init__(self, cor, modelo):
        self.cor = cor
        self.modelo = modelo
        self.ligado = False
    
    def descricao(self):
        print(f'Meu modelo é {self.modelo} e minha cor é {self.cor}')

    def ligar(self):
        self.ligado = True
        print('O veiculo foi ligado')
    
    def desligar(self):
        self.ligado = False
        print('O veiculo foi desligado')
    
    def pintar(self, nova_cor):
        self.cor = nova_cor
        print(f'O veiculo foi pintado. Nova cor: {self.cor}')

class Carro(Veiculo):

    rodas = 4

    def descricao(self):
        print(f'Eu sou umn carro, meu modelo é {self.modelo} e minha cor é {self.cor}')


meu_carro = Carro(cor='prata', modelo='peugeot')
meu_carro.descricao()
meu_carro.ligar()
meu_carro.desligar()
meu_carro.pintar('Vermelho')
print(meu_carro.rodas)



