FROM node:18

WORKDIR /app

# Instala dependências
COPY package*.json ./
RUN npm install



EXPOSE 3000

# Comando para iniciar o modo dev (hot reload)
CMD ["npm", "start"]
