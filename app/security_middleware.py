# app/security_middleware.py
import time
import hashlib
from flask import request, jsonify
import logging
from datetime import datetime, timedelta
import re
import json   # Necessário para montar respostas JSON
import io  # <-- ADICIONE ESTA LINHA

class SecurityMiddleware:
    """Middleware de segurança para proteção adicional
    - Bloqueia IPs com muitas falhas
    - Detecta SQL injection básico (ainda que use MongoDB)
    - Identifica flood de requisições
    - Valida User-Agent
    """

    def __init__(self, app):
        self.app = app
        self.failed_attempts = {}       # Contador de falhas por IP
        self.blocked_ips = {}           # IPs bloqueados com timestamp de desbloqueio
        self.suspicious_activities = {} # Histórico de atividades suspeitas por IP
        
        # Configurações de segurança
        self.MAX_FAILED_ATTEMPTS = 10  # Número máximo de falhas antes de bloquear
        self.BLOCK_TIME = 900          # Tempo de bloqueio em segundos (15 minutos)
        self.SUSPICIOUS_THRESHOLD = 5  # Limite de atividades suspeitas

    def __call__(self, environ, start_response):
        """Intercepta TODAS as requisições antes do Flask"""
        client_ip = self.get_client_ip(environ)
        
        # 1. Bloqueio por tentativas anteriores
        if self.is_ip_blocked(client_ip):
            return self.blocked_response(start_response)
        
        # 2. Verificação de atividades suspeitas
        if self.check_suspicious_activity(environ, client_ip):
            return self.suspicious_response(start_response)
        
        # 3. Caso não haja suspeita, segue o fluxo normal
        return self.app(environ, start_response)

    def get_client_ip(self, environ):
        """Obtém IP real do cliente considerando proxies"""
        for header in ['HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP', 'REMOTE_ADDR']:
            ip = environ.get(header)
            if ip:
                # Se vier lista de IPs (proxy), pega o primeiro
                if ',' in ip:
                    ip = ip.split(',')[0].strip()
                return ip
        return 'unknown'

    def is_ip_blocked(self, client_ip):
        """Verifica se o IP ainda está bloqueado"""
        if client_ip in self.blocked_ips:
            block_until = self.blocked_ips[client_ip]
            if time.time() < block_until:
                return True
            else:
                # Bloqueio expirado → remove da lista
                del self.blocked_ips[client_ip]
        return False

    def check_suspicious_activity(self, environ, client_ip):
        """Detecta comportamentos suspeitos na requisição"""
        path = environ.get('PATH_INFO', '')
        method = environ.get('REQUEST_METHOD', '')
        user_agent = environ.get('HTTP_USER_AGENT', '')

        # 1. User-Agent suspeito ou ausente
        if not user_agent or len(user_agent) < 10:
            self.record_suspicious_activity(client_ip, "Missing/invalid User-Agent")
            return True

        # 2. Detecta padrões de Injeção (SQL/NoSQL) na query ou body
        if self.detect_injection_attempt(environ):
            self.record_suspicious_activity(client_ip, "Injection attempt detected")
            return True

        # 3. Alta frequência de acessos em endpoints sensíveis (/login, /register, etc.)
        if self.is_sensitive_path(path) and self.is_high_frequency(client_ip):
            self.record_suspicious_activity(client_ip, "High frequency on sensitive path")
            return True

        return False

    def detect_injection_attempt(self, environ):
        """
        Detecta tentativas de injeção (SQL e NoSQL), ignorando o corpo
        de requisições de upload de arquivos para evitar falsos positivos.
        """
        # Padrões de NoSQL Injection (focados em operadores perigosos e JS)
        nosql_patterns = [
            r'\$where',          # Operador $where, muito perigoso
            r'mapReduce',        # Comando MapReduce
            r'group',            # Operador de group
            r'sleep\(',          # Tentativas de ataques de tempo (timing attacks)
            r'benchmark\('       
        ]

        # Padrões de SQL Injection (mantidos como defesa em profundidade)
        sql_patterns = [
            r'union.*select', r'select.*from', r'insert.*into',
            r'delete.*from', r'drop.*table', r'--', r'/\*',
            r'waitfor.*delay', r'xp_cmdshell'
        ]
        
        # Combinamos ambas as listas para uma verificação completa
        all_patterns = nosql_patterns + sql_patterns
        
        # 1. Verifica a query string (parâmetros na URL)
        query_string = environ.get('QUERY_STRING', '')
        for pattern in all_patterns:
            if re.search(pattern, query_string, re.IGNORECASE):
                logging.warning(f"Injection attempt detected in query string: {query_string}")
                return True

        # 2. Verifica o corpo (body) da requisição, EXCETO para upload de arquivos
        if environ['REQUEST_METHOD'] in ['POST', 'PUT']:
            content_type = environ.get('CONTENT_TYPE', '')

            # ESSA É A REGRA QUE PERMITE O UPLOAD DE PDF:
            # Se for um upload de arquivo, não verifique o corpo para evitar falsos positivos.
            if 'multipart/form-data' in content_type:
                return False

            try:
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                if content_length > 0:
                    request_body_bytes = environ['wsgi.input'].read(content_length)

                    # SOLUÇÃO: Substitui o stream original por um novo, em memória
                    environ['wsgi.input'] = io.BytesIO(request_body_bytes)

                    request_body_str = request_body_bytes.decode('utf-8', 'ignore')

                    for pattern in all_patterns:
                        if re.search(pattern, request_body_str, re.IGNORECASE):
                            logging.warning("Injection attempt detected in request body.")
                            return True
            except Exception as e:
                logging.error(f"Error reading request body in middleware: {e}")
                pass
        
        return False
    def is_sensitive_path(self, path):
        """Define rotas críticas que merecem monitoramento mais rigoroso"""
        sensitive_paths = [
            '/login',
            '/register',
            '/upload',
            '/users/',
            '/products/'
        ]
        return any(path.startswith(p) for p in sensitive_paths)

    def is_high_frequency(self, client_ip):
        """Verifica se um IP está enviando requisições em excesso"""
        current_time = time.time()
        if client_ip not in self.suspicious_activities:
            self.suspicious_activities[client_ip] = []
        
        self.suspicious_activities[client_ip].append(current_time)
        # Mantém apenas últimas requisições de 60s
        self.suspicious_activities[client_ip] = [
            t for t in self.suspicious_activities[client_ip] if current_time - t < 60
        ]
        return len(self.suspicious_activities[client_ip]) > 30

    def record_suspicious_activity(self, client_ip, reason):
        """Registra atividade suspeita e aplica bloqueio se necessário"""
        logging.warning(f"Suspicious activity detected - IP: {client_ip}, Reason: {reason}")
        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = 0
        self.failed_attempts[client_ip] += 1

        # Bloqueia após muitas falhas
        if self.failed_attempts[client_ip] >= self.MAX_FAILED_ATTEMPTS:
            self.blocked_ips[client_ip] = time.time() + self.BLOCK_TIME
            logging.warning(f"IP blocked: {client_ip} for {self.BLOCK_TIME} seconds")

    def blocked_response(self, start_response):
        """Resposta para IPs bloqueados"""
        start_response('429 Too Many Requests', [
            ('Content-Type', 'application/json'),
            ('Retry-After', str(self.BLOCK_TIME))
        ])
        return [json.dumps({
            "error": "Acesso temporariamente bloqueado",
            "message": "Muitas tentativas suspeitas detectadas. Tente novamente em 15 minutos.",
            "retry_after": self.BLOCK_TIME
        }).encode()]

    def suspicious_response(self, start_response):
        """Resposta para atividade suspeita"""
        start_response('400 Bad Request', [
            ('Content-Type', 'application/json')
        ])
        return [json.dumps({
            "error": "Atividade suspeita detectada",
            "message": "Sua requisição foi identificada como suspeita."
        }).encode()]

# Função auxiliar para inicializar o middleware
def init_security_middleware(app):
    """Ativa o middleware de segurança WSGI na aplicação Flask"""
    app.wsgi_app = SecurityMiddleware(app.wsgi_app)
    logging.info("Security middleware initialized")
    return app
