# Dockerfile (backend)

# 1. IMAGEM BASE
# Utiliza uma imagem Python leve e otimizada.
FROM python:3.11-slim

# 2. DIRETÓRIO DE TRABALHO
# Define o diretório padrão dentro do container.
WORKDIR /app

# 3. VARIÁVEL DE AMBIENTE
# Garante que os logs do Python sejam enviados diretamente para o console do container.
# Essencial para que a Render possa exibir seus logs.
ENV PYTHONUNBUFFERED=1

# 4. INSTALAÇÃO DE DEPENDÊNCIAS
# Copia e instala as dependências primeiro para aproveitar o cache do Docker.
# Se o requirements.txt não mudar, o Docker não re-instala tudo a cada build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. COPIA DO CÓDIGO DA APLICAÇÃO
# Copia todo o código do seu projeto para o diretório de trabalho.
COPY . .

# 6. COMANDO DE EXECUÇÃO (A GRANDE MUDANÇA)
# Este é o comando que a Render irá executar quando o container iniciar.
# - gunicorn: O servidor de produção.
# - --workers 3: (Opcional, mas recomendado) Número de processos para lidar com requisições. Um bom começo é 2-4.
# - --bind 0.0.0.0:$PORT: Diz ao Gunicorn para escutar em todas as interfaces de rede na porta
#   que a Render fornecer através da variável de ambiente $PORT. É crucial não fixar a porta!
# - run:app: O ponto de entrada da aplicação. Significa: "No arquivo run.py, encontre a variável 'app'".
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:$PORT", "run:app"]