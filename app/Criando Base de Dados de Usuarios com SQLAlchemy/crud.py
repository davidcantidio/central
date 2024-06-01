from pathlib import Path

from sqlalchemy import create_engine, String, Boolean, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

from werkzeug.security import generate_password_hash, check_password_hash

pasta_atual = Path(__file__).parent
PATH_TO_BD = pasta_atual / 'bd_usuarios.sqlite'

class Base(DeclarativeBase):
    pass

class Usuario(Base):
    __tablename__ = 'usuarios'

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(30))
    senha: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(30))
    acesso_gestor: Mapped[bool] = mapped_column(Boolean(), default=False)

    def __repr__(self):
        return f"Usuario({self.id=}, {self.nome=})"
    
    def define_senha(self, senha):
        self.senha = generate_password_hash(senha)

    def verifica_senha(self, senha):
        return check_password_hash(self.senha, senha)
    
    
engine = create_engine(f'sqlite:///{PATH_TO_BD}')
Base.metadata.create_all(bind=engine)


# CRUD ======================
def cria_usurios(
        nome,
        senha,
        email,
        **kwargs
):
    with Session(bind=engine) as session:
        usuario = Usuario(
            nome=nome,
            email=email,
            **kwargs
        )
        usuario.define_senha(senha)
        session.add(usuario)
        session.commit()

def le_todos_usuarios():
    with Session(bind=engine) as session:
        comando_sql = select(Usuario)
        usuarios = session.execute(comando_sql).fetchall()
        usuarios = [user[0] for user in usuarios]
        return usuarios

def le_usuario_por_id(id):
    with Session(bind=engine) as session:
        comando_sql = select(Usuario).filter_by(id=id)
        usuarios = session.execute(comando_sql).fetchall()
        return usuarios[0][0]

def modifica_usuario_old(
        id, 
        nome=None,
        senha=None,
        email=None,
        acesso_gestor=None
        ):
    with Session(bind=engine) as session:
        comando_sql = select(Usuario).filter_by(id=id)
        usuarios = session.execute(comando_sql).fetchall()
        for usuario in usuarios:
            if nome:
                usuario[0].nome = nome
            if senha:
                usuario[0].senha = senha
            if email:
                usuario[0].email = email
            if not acesso_gestor is None:
                usuario[0].acesso_gestor = acesso_gestor
        session.commit()

def modifica_usuario(
        id, 
        **kwargs
        ):
    with Session(bind=engine) as session:
        comando_sql = select(Usuario).filter_by(id=id)
        usuarios = session.execute(comando_sql).fetchall()
        for usuario in usuarios:
            for key, value in kwargs.items():
                if key == 'senha':
                    usuario[0].define_senha(value)
                else:
                    setattr(usuario[0], key, value)
        session.commit()

def deleta_usuario(id):
    with Session(bind=engine) as session:
        comando_sql = select(Usuario).filter_by(id=id)
        usuarios = session.execute(comando_sql).fetchall()
        for usuario in usuarios:
            session.delete(usuario[0])
        session.commit()


if __name__ == '__main__':
    # cria_usurios(
    #     'Luiza Cherobini',
    #     senha='minha_senha',
    #     email='meuemail.com',
    # )

    # usuarios = le_todos_usuarios()
    # usuario_0 = usuarios[0]
    # print(usuario_0)
    # print(usuario_0.nome, usuario_0.senha, usuario_0.email)

    # usuario_adriano = le_usuario_por_id(id=1)
    # print(usuario_adriano)
    # print(usuario_adriano.nome, usuario_adriano.senha, usuario_adriano.email)

    # modifica_usuario(id=1, nome='Novo nome do Adriano', senha='Nova senha adriano')

    # cria_usurios(
    #     'Adriano Soares',
    #     senha='minha_senha',
    #     email='meuemail.com',
    # )

    cria_usurios(
        'Juliano Faccioni',
        senha='juli',
        email='meuemail.com',
    )

    cria_usurios(
        'Luiza Cherobini',
        senha='lu',
        email='meuemail.com',
    )


    usuario_adriano = le_usuario_por_id(id=1)
    print(usuario_adriano.verifica_senha('sdfsdfsdfsfs'))


    
