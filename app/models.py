from datetime import datetime
from bson.objectid import ObjectId

class User:
    collection_name = 'users'

    def __init__(self, username, email, password_hash, role,
                 cpf=None, empresa=None, setor=None, data_de_nascimento=None, planta=None,
                 _id=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.cpf = cpf
        self.empresa = empresa
        self.setor = setor
        self.data_de_nascimento = data_de_nascimento
        self.planta = planta
        self._id = _id

    def to_dict(self):
        user_dict = {
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
            "cpf": self.cpf,
            "empresa": self.empresa,
            "setor": self.setor,
            "data_de_nascimento": self.data_de_nascimento,
            "planta": self.planta
        }
        if self._id:
            user_dict["_id"] = str(self._id)   # 👈 Convertendo para string
        return user_dict

    @classmethod
    def from_dict(cls, data):
        return cls(
            username=data.get('username'),
            email=data.get('email'),
            password_hash=data.get('password_hash'),
            role=data.get('role'),
            cpf=data.get('cpf'),
            empresa=data.get('empresa'),
            setor=data.get('setor'),
            data_de_nascimento=data.get('data_de_nascimento'),
            planta=data.get('planta'),
            _id=data.get('_id')
        )

    @classmethod
    def collection(cls):
        from . import db
        return db[cls.collection_name]


class Product:
    collection_name = 'products'

    def __init__(self, codigo, qtade_maxima_armazenada, nome_do_produto, fornecedor,
                 estado_fisico, local_de_armazenamento, substancias,
                 palavra_de_perigo, categoria, status, created_by_user_id,
                 perigos_fisicos=None, perigos_saude=None, perigos_meio_ambiente=None,
                 pdf_url=None, pdf_s3_key=None, empresa=None, _id=None, created_at=None):
        self.codigo = codigo
        self.qtade_maxima_armazenada = qtade_maxima_armazenada
        self.nome_do_produto = nome_do_produto
        self.fornecedor = fornecedor
        self.estado_fisico = estado_fisico
        self.local_de_armazenamento = local_de_armazenamento
        self.substancias = substancias or []
        self.perigos_fisicos = perigos_fisicos or []
        self.perigos_saude = perigos_saude or []
        self.perigos_meio_ambiente = perigos_meio_ambiente or []
        self.palavra_de_perigo = palavra_de_perigo
        self.categoria = categoria
        self.status = status
        self.created_by_user_id = created_by_user_id
        self.pdf_url = pdf_url
        self.pdf_s3_key = pdf_s3_key
        self.empresa = empresa
        self._id = _id
        self.created_at = created_at if created_at is not None else datetime.utcnow()

    def to_dict(self):
        product_dict = {
            "codigo": self.codigo,
            "qtade_maxima_armazenada": self.qtade_maxima_armazenada,
            "nome_do_produto": self.nome_do_produto,
            "fornecedor": self.fornecedor,
            "estado_fisico": self.estado_fisico,
            "local_de_armazenamento": self.local_de_armazenamento,
            "substancias": self.substancias,
            "perigos_fisicos": self.perigos_fisicos,
            "perigos_saude": self.perigos_saude,
            "perigos_meio_ambiente": self.perigos_meio_ambiente,
            "palavra_de_perigo": self.palavra_de_perigo,
            "categoria": self.categoria,
            "status": self.status,
            "created_by_user_id": str(self.created_by_user_id) if self.created_by_user_id else None,  # 👈 fix
            "pdf_url": self.pdf_url,
            "pdf_s3_key": self.pdf_s3_key,
            "empresa": self.empresa,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
        if self._id:
            product_dict["_id"] = str(self._id)  # 👈 fix
        return product_dict

    @classmethod
    def from_dict(cls, data):
        created_at_data = data.get("created_at")
        if isinstance(created_at_data, str):
            try:
                created_at_data = datetime.fromisoformat(created_at_data)
            except ValueError:
                pass

        return cls(
            codigo=data.get('codigo'),
            qtade_maxima_armazenada=data.get('qtade_maxima_armazenada'),
            nome_do_produto=data.get('nome_do_produto'),
            fornecedor=data.get('fornecedor'),
            estado_fisico=data.get('estado_fisico'),
            local_de_armazenamento=data.get('local_de_armazenamento'),
            substancias=data.get('substancias', []),
            perigos_fisicos=data.get('perigos_fisicos', []),
            perigos_saude=data.get('perigos_saude', []),
            perigos_meio_ambiente=data.get('perigos_meio_ambiente', []),
            palavra_de_perigo=data.get('palavra_de_perigo'),
            categoria=data.get('categoria'),
            status=data.get('status'),
            created_by_user_id=data.get('created_by_user_id'),
            pdf_url=data.get('pdf_url'),
            pdf_s3_key=data.get('pdf_s3_key'),
            empresa=data.get('empresa'),
            _id=data.get('_id'),
            created_at=created_at_data
        )

    @classmethod
    def collection(cls):
        from . import db
        return db[cls.collection_name]
