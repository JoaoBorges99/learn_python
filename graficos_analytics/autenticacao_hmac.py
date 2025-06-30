import hmac
import hashlib
import base64
import os
from dotenv import load_dotenv
from fastapi import Request, Header, HTTPException

load_dotenv()

async def auth_request (request : Request, assinatura_cliente:str = Header(..., alias="X-HMAC-SIGNATURE")):
    dados = await request.body()
    chave = os.getenv("SECRET_KEY")

    if chave is None or assinatura_cliente is None:
        raise HTTPException(detail={"error": "Erro interno do servidor"}, status_code=500)
    try:
        server_security_key = hmac.new(chave.encode(), dados, hashlib.sha256).digest()
        server_signature = base64.b64encode(server_security_key).decode()
        comparacao = hmac.compare_digest(server_signature, assinatura_cliente)
        if not assinatura_cliente or not comparacao:
            raise HTTPException(detail={"error": "Assinatura inválida"}, status_code=200)
        return True
    except Exception as e:
        raise HTTPException(detail={"error":"Não foi possivel autenticar"}, status_code=401)