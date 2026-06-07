# Fast Task Manager

O Fast Task Manager é uma ferramenta de produtividade pessoal desenvolvida para organização de projetos e tarefas. Com uma interface inspirada no design minimalista de ferramentas como o Notion e Trello, o foco é a funcionalidade e o acesso rápido a informações críticas.
O projeto foi construído utilizando uma arquitetura que permite seu uso como uma aplicação Web completa ou como um aplicativo Desktop nativo.

## Screenshots

![Login](static/login_image.png)
![Dashboard](static/dashboard_image_com_tarefas.png)
![Projetos](static/projetos.png)
![Calendário](static/calendario.png)

# Tecnologias Utilizadas
- **Backend:** Python com FastAPI
- **Banco de Dados:** SQLite
- **UI/UX:** HTML5, CSS3, JavaScript
- **Desktop:** PyWebView
- **Empacotamento:** PyInstaller
# Objetivo do Projeto

Este software nasceu para ser um gerenciador de tarefas pessoal, funcional e offline. A ausência de camadas desnecessárias de colaboração (teams/roles) garante que o sistema seja focado na organização do próprio usuário, tornando-o rápido, leve e intuitivo.

# Como rodar o código

## 1. Pré-requisitos
    Ter o Python 3.x instalado.
    Ter o Git instalado.

## 2. Clonando o repositório
```bash
git clone https://github.com/HayziVV/Fast-Task-Manager.git
cd Fast-Task-Manager
```

## 3. Configuração do ambiente virtual
```Bash
python -m venv venv
venv\Scripts\activate.bat   # windows
source venv/bin/activate    # Linux/macOS

pip install -r requirements.txt
```

## 4. Iniciando o servidor
### Para rodar a aplicação no modo desenvolvimento:
```Bash
python main.py
```
### O sistema iniciará o servidor FastAPI automaticamente e abrirá a janela desktop.

# Gerando o Executável (.exe)
### Caso queira gerar um executável para rodar em qualquer máquina Windows sem precisar do Python instalado:

### 1 - Execute o comando de empacotamento:

```Bash
pyinstaller --noconsole --onedir --add-data "static;static" --add-data "templates;templates" --icon=static/favicon.ico main.py
```

### 3 - O seu executável estará na pasta /dist/main/main.exe

# Estrutura do Projeto

```text
Fast-Tasks-Manager-main/
|---- Fast-Task-Manager-main/
|     |
|     |---- routers/
|     |     |---- auth.py
|     |     |---- notes.py
|     |     |---- projects.py
|     |     |---- tasks.py
|     |     |---- views.py
|     |---- static/
|     |     |---- css/
|     |     |     |---- base.css
|     |     |     |---- style.css
|     |     |---- js/
|     |     |     |---- auth.js
|     |     |     |---- notes.js
|     |     |     |---- projects.js
|     |     |     |---- script.js
|     |     |     |---- tasks.js
|     |     |---- favicon.ico
|     |---- templates/
|     |     |---- base.html
|     |     |---- calendar.html
|     |     |---- dashboard.html
|     |     |---- notes.html
|     |     |---- project_tasks.html
|     |     |---- projects.html
|     |     |---- sign_in.html
|     |     |---- sign_up.html
|     |     |---- tasks.html
|     |---- database.py
|     |---- main.py
|     |---- README.md
|     |---- requirements.txt
|     |---- .gitignore
```

## 🚧 Roadmap
- [ ] Exportação para PDF e TXT (pausado após migração para PyWebView)
- [ ] Modo claro
- [ ] Melhoria para o editor de texto da telas de notas
- [ ] Integração com modelo de IA local (ex: Ollama ou LM Studio) para resumo de notas