<p align="center">
  <img src="sinistros/static/sinistros/img/orbis-logo.png" alt="Orbis — Gestão integrada de sinistros" width="420">
</p>

# Orbis · Gestão integrada de sinistros

Oi! Eu sou a Ester, e este é o **Orbis**, um sistema web que estou construindo para
organizar o dia a dia de um setor de sinistros. Ele também é o meu projeto para
aprender back-end de verdade.

> 🚧 Em desenvolvimento · versão atual **v0.2** · todos os dados do projeto são **fictícios**.

---

## Por que eu criei o Orbis

Trabalho no setor de sinistros de uma empresa de proteção veicular. O setor tem
vários subsetores (regulação, análise, autorização, vidros, notas, despachante,
reembolso e atendimento), e cada um acabava trabalhando do seu jeito, com
planilhas separadas.

Na prática, isso gerava perguntas que todo mundo do setor conhece:

- *"Onde está esse processo agora?"*
- *"Com quem ele está?"*
- *"Faz quanto tempo que ele está parado?"*
- *"De quem é a vez de pegar o próximo?"*

Eu queria um lugar só onde essas respostas aparecessem sozinhas. E, como eu já
sabia um pouco de front-end e estava estudando Python, decidi construir esse lugar
eu mesma e aprender back-end no caminho.

## A ideia: uma "torre de controle" do sinistro

Em vez de enxergar subsetores isolados, o Orbis enxerga **um fluxo único**, e cada
processo anda por ele:

```
CADASTRO → REGULAÇÃO → ANÁLISE → AUTORIZAÇÃO → EXECUÇÃO → DOCUMENTAÇÃO → CONCLUSÃO
```

Cada processo é identificado pelo **protocolo** e guarda tudo o que acontece com ele:
quem cadastrou, quem é a responsável, em que etapa está, qual é o prazo, quais
documentos foram anexados e o histórico completo de movimentações.

## Como funciona hoje (v0.2)

**🔐 Login**
Cada pessoa entra com o seu próprio usuário. Cada colaboradora pertence a um
subsetor e tem um papel: colaboradora, líder ou supervisão.

**🗂️ Minha mesa**
A primeira tela depois do login mostra **só os processos que estão comigo**,
separados por situação: atrasados, vencem hoje, no prazo e sem prazo. No topo de
todas as telas tem um 🔔 com quantos processos eu tenho em aberto.

**🔎 Busca por protocolo**
Digitou o protocolo, o processo abre direto. Também dá para buscar por placa ou
pelo nome do associado.

**📝 Cadastro do processo**
O sistema não deixa cadastrar dois processos com o mesmo protocolo e já padroniza a
placa (`abc-1d23` vira `ABC1D23`).

**📎 Documentos**
Cada processo tem a sua pasta de anexos: BO, CNH, fotos, orçamentos, notas fiscais…
Só quem está logado consegue abrir os arquivos, e só líderes e supervisão podem
excluir.

**🕓 Histórico**
Tudo fica registrado automaticamente: cadastro, alterações, anexos e exclusões. Dá
para escrever anotações também (por exemplo, "associado enviou o BO por e-mail").
Assim ninguém precisa perguntar "o que aconteceu com esse processo?".

**🟢 Disponível / indisponível**
Quem está de férias, de atestado ou de folga pode ser marcada como indisponível.
Esse é o primeiro passo para as filas automáticas.

## O que vem por aí

- [x] **v0.1** – primeira versão: modelos, lista e detalhe dos processos
- [x] **v0.2** – login, Minha mesa, busca por protocolo, anexos e identidade visual
- [ ] **v0.3** – **filas "quem está na vez"**
  - *Regulação:* vai para quem tem **menos** regulações abertas
  - *Análise:* quem envia escolhe o subsetor, e dentro dele vai por **rodízio**
  - *Atendimento:* **rodízio** puro
  - Quem está indisponível é pulada automaticamente
- [ ] **v0.4** – **transferência** de processos (um ou todos de uma vez), levando o histórico e os documentos
- [ ] **v0.5** – **alertas** dentro do sistema (processo novo, prazo vencendo)
- [ ] **Depois** – painel da supervisão, prazos por etapa, alertas de processo parado
  (48h → responsável, 72h → líder, 96h → supervisão), modelos de mensagem e
  dashboard com indicadores

## Com o que eu construí

| Parte | Tecnologia | Por quê |
|---|---|---|
| Back-end | **Python + Django** | Já vem com login, segurança, banco de dados e painel admin prontos, e Python é a linguagem que estou estudando |
| Banco de dados | **SQLite** (estudo) → PostgreSQL (produção) | O SQLite não precisa instalar nada para começar |
| Front-end | **HTML + CSS** com os templates do Django | Uso o que eu já sabia de front-end |
| Visual | Paleta grafite + ciano, fonte Manrope | Todas as cores ficam em variáveis no começo do CSS |

## O que eu estou aprendendo com este projeto

- Como uma página web nasce no servidor: **URL → view → banco → template → navegador**
- Modelar dados de um problema real: tabelas, relações e por que guardar o **histórico**
- Formulários e validações (protocolo repetido, placa, tipo e tamanho de arquivo)
- Login, permissões e cuidados de segurança (arquivos protegidos, chaves fora do código)
- Organizar o projeto, usar ambiente virtual, terminal e Git

---

## Quer rodar no seu computador?

### 1. Instalar (só na primeira vez)

1. Instale o **Python 3.12 ou mais novo**: https://www.python.org/downloads/
   (no Windows, marque a caixinha **"Add Python to PATH"** na instalação)
2. Baixe o projeto (`git clone` ou o zip) e abra um terminal dentro da pasta (a que tem o `manage.py`).

```bash
# cria um "ambiente virtual": uma caixinha só deste projeto com as bibliotecas dele
python -m venv venv

# ativa a caixinha (aparece "(venv)" no começo da linha)
source venv/Scripts/activate   # Windows (Git Bash)
venv\Scripts\activate          # Windows (CMD / PowerShell)
source venv/bin/activate       # Mac / Linux

# instala o Django
pip install -r requirements.txt

# cria as tabelas no banco (arquivo db.sqlite3)
python manage.py migrate

# coloca dados fictícios para testar
python manage.py popular_dados
```

### 2. Ligar o sistema

```bash
source venv/Scripts/activate   # ative o ambiente (veja acima para o seu sistema)
python manage.py runserver
```

Abra **http://127.0.0.1:8000** no navegador. Para desligar, use **Ctrl + C** no terminal.

| Quem | Usuário | Senha |
|---|---|---|
| Supervisão (acessa o Admin) | `admin` | `admin123` |
| Líder | `ana` | `teste123` |
| Colaboradoras | `bruno`, `carla`, `diego`… | `teste123` |

> Essas senhas são **só para teste local**. Em um sistema publicado, elas precisam ser trocadas.

No **Admin** (http://127.0.0.1:8000/admin/) dá para cadastrar subsetores e
colaboradoras e marcar quem está indisponível.

### Comandos úteis

| Comando | Para quê |
|---|---|
| `python manage.py runserver` | Liga o sistema |
| `python manage.py makemigrations` | Depois de mudar o `models.py` |
| `python manage.py migrate` | Aplica as mudanças no banco |
| `python manage.py popular_dados` | Recria os dados fictícios |
| `python manage.py createsuperuser` | Cria outro usuário admin |

---

## Por dentro do código

```
orbis/
├── manage.py                  ← "controle remoto" do projeto
├── config/
│   ├── settings.py            ← configurações (idioma, apps, pasta dos anexos)
│   └── urls.py                ← rotas principais: admin, login, logout
├── media/                     ← os anexos ficam aqui (criada sozinha, fora do Git)
└── sinistros/                 ← o app principal
    ├── models.py              ← ⭐ as tabelas do banco: Subsetor, Colaborador, Processo, Movimentacao, Anexo
    ├── forms.py               ← formulários e validações
    ├── views.py               ← o "cérebro" de cada página
    ├── urls.py                ← endereço → view
    ├── context_processors.py  ← dados que aparecem em todas as páginas (o 🔔)
    ├── admin.py               ← como os dados aparecem no /admin
    ├── templates/sinistros/   ← as telas (os arquivos com "_" são pedaços reaproveitáveis)
    ├── static/sinistros/      ← CSS e logos
    └── management/commands/popular_dados.py  ← gera os dados fictícios
```

Se você quiser entender o projeto, sugiro ler nesta ordem:
`models.py` → `forms.py` → `urls.py` → `views.py` → `templates/sinistros/detalhe.html`.
Os arquivos têm comentários em português explicando cada parte.

**Como um anexo é enviado:**
```
Formulário com enctype="multipart/form-data"  (detalhe.html)
   → views.detalhe_processo recebe o arquivo em request.FILES
   → forms.AnexoForm confere extensão e tamanho (máx. 15 MB)
   → salva em media/anexos/<protocolo>/arquivo.pdf
   → registra "Anexou ..." no histórico
Para baixar: views.baixar_anexo só entrega o arquivo para quem está logado.
```

**Personalizar:**
- **Cores:** todas ficam no começo de `sinistros/static/sinistros/estilo.css`, em `:root`.
- **Logos:** em `sinistros/static/sinistros/img/` (`orbis-logo.png`, `orbis-simbolo.png`, `favicon.png`).
  É só substituir mantendo os mesmos nomes.

## Segurança e dados

- Este repositório **não contém dados reais**. O banco (`db.sqlite3`) e os anexos
  (`media/`) ficam de fora pelo `.gitignore`.
- A `SECRET_KEY` e o `DEBUG` vêm de variáveis de ambiente em produção
  (`DJANGO_SECRET_KEY` e `DJANGO_DEBUG=0`). O valor que está no código é só para estudo.
- Antes de qualquer uso com dados reais, o sistema vai passar por ajustes de produção
  (PostgreSQL, backup, HTTPS, permissões) e pela aprovação de quem é responsável
  pelos dados, conforme a LGPD.

---

<p align="center">Feito com ☕ e muita vontade de aprender, por <strong>Ester Santos</strong>.</p>
