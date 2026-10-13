<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-dark.svg" />
  <img src="assets/header-light.svg" width="100%" alt="Luiz Felipe · Ciência da Computação · UFPel" />
</picture>

Estudo Ciência da Computação na UFPel, em Pelotas (RS). Gosto de matemática, de arquitetura de computadores e de sistemas operacionais: memória, cache, threads, concorrência. Programo mais em C, C++ e Python.

<p>
  <a href="https://www.linkedin.com/in/luiz-felipe-pereira-bandeira-8a51761b6/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI%2BPHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0yMC40NDcgMjAuNDUyaC0zLjU1NHYtNS41NjljMC0xLjMyOC0uMDI3LTMuMDM3LTEuODUyLTMuMDM3LTEuODUzIDAtMi4xMzYgMS40NDUtMi4xMzYgMi45Mzl2NS42NjdIOS4zNTFWOWgzLjQxNHYxLjU2MWguMDQ2Yy40NzctLjkgMS42MzctMS44NSAzLjM3LTEuODUgMy42MDEgMCA0LjI2NyAyLjM3IDQuMjY3IDUuNDU1djYuMjg2ek01LjMzNyA3LjQzM2MtMS4xNDQgMC0yLjA2My0uOTI2LTIuMDYzLTIuMDY1IDAtMS4xMzguOTItMi4wNjMgMi4wNjMtMi4wNjMgMS4xNCAwIDIuMDY0LjkyNSAyLjA2NCAyLjA2MyAwIDEuMTM5LS45MjUgMi4wNjUtMi4wNjQgMi4wNjV6bTEuNzgyIDEzLjAxOUgzLjU1NVY5aDMuNTY0djExLjQ1MnpNMjIuMjI1IDBIMS43NzFDLjc5MiAwIDAgLjc3NCAwIDEuNzI5djIwLjU0MkMwIDIzLjIyNy43OTIgMjQgMS43NzEgMjRoMjAuNDUxQzIzLjIgMjQgMjQgMjMuMjI3IDI0IDIyLjI3MVYxLjcyOUMyNCAuNzc0IDIzLjIgMCAyMi4yMjIgMGguMDAzeiIvPjwvc3ZnPg%3D%3D" alt="LinkedIn" /></a>
  <a href="https://codeforces.com/profile/root.svp"><img src="https://img.shields.io/badge/Codeforces-1F8ACB?style=for-the-badge&logo=codeforces&logoColor=white" alt="Codeforces" /></a>
</p>

## Matemática

- Na iniciação científica, trabalhei no projeto *Modelagem matemática em controle populacional*, estudando EDPs elípticas e parabólicas e métodos de perturbação.
- Simulei em Python o oscilador fracamente amortecido $`\ddot{x} + 2\varepsilon\dot{x} + x = 0`$ e comparei o método das médias e o de escalas múltiplas com a solução exata. É a curva lá de cima.
- Montei slides sobre espaços de Banach, dual e bidual para as reuniões de análise funcional.
- Também estudo análise no ℝⁿ e teoria dos números.

## Arquitetura e sistemas

- **Cache:** com o SimpleScalar, medi como cache unificada ou separada, associatividade, política de substituição (LRU, FIFO, aleatória), tamanho de bloco e uma L2 mudam o número de misses nos benchmarks do gcc e do ijpeg. Um script em Python automatizou as execuções.
- **Sistemas operacionais:** threads com pthreads, mutex, barreiras e o jantar dos filósofos.
- **C e C++:** implementei do zero estruturas como árvore binária de busca e tabela hash.

## Programação competitiva

Treino no Codeforces e no AtCoder, quase sempre em C++ ou Python.

<a href="https://codeforces.com/profile/root.svp">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/codeforces-dark.svg" />
    <img src="assets/codeforces-light.svg" width="100%" alt="Estatísticas no Codeforces: rating, problemas resolvidos, evolução por contest e dificuldade dos problemas" />
  </picture>
</a>

<sub>O card se atualiza sozinho uma vez por dia com a API do Codeforces.</sub>

## Projetos

<table>
  <tr>
    <td width="33%" valign="top">
      <h3>Librarian</h3>
      <p><code>C++17</code> <code>Qt5</code> <code>SQLite</code></p>
      <p>App nativo onde minha biblioteca de PDFs vira um salão para andar, com uma estante por assunto, busca, favoritos e notas. Tudo desenhado com QPainter, com colisão e câmera.</p>
    </td>
    <td width="33%" valign="top">
      <h3>cf-trainer</h3>
      <p><code>C17</code> <code>Bash</code></p>
      <p>Treinador de Codeforces no terminal. Puxa meu histórico pela API, monta o treino do dia na minha faixa de rating e mostra em quais tags eu mais erro. Sem banco de dados, só arquivos TSV.</p>
    </td>
    <td width="33%" valign="top">
      <h3>Atlas PDF</h3>
      <p><code>Python</code> <code>SQLite</code> <code>Electron</code></p>
      <p>Biblioteca de PDFs para Linux. Indexa os arquivos, separa por assunto e encontra duplicatas.</p>
    </td>
  </tr>
</table>

No GitHub:

- [modelagem](https://github.com/luizfelipejs/modelagem): equações diferenciais (mapa logístico, caos) e modelos estatísticos em Python.
- [livros](https://github.com/luizfelipejs/livros): materiais de estudo de matemática.
- [Twitter-webscrapping](https://github.com/luizfelipejs/Twitter-webscrapping): busca termos no X/Twitter com Python e Selenium e salva os textos em JSON.

## Ferramentas

<img src="https://skillicons.dev/icons?i=c,cpp,linux,bash,qt,py,latex,sqlite,react,electron" alt="C, C++, Linux, Bash, Qt, Python, LaTeX, SQLite, React, Electron" />

## Contato

Se quiser conversar sobre matemática, arquitetura de computadores ou programação, me chama no [LinkedIn](https://www.linkedin.com/in/luiz-felipe-pereira-bandeira-8a51761b6/).
