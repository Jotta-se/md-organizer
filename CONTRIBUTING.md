# Contribuindo com o MD Organizer

Obrigado por considerar contribuir com este projeto! Siga os passos abaixo para submeter correções ou melhorias.

## Como contribuir

1. Faça um *Fork* do projeto no GitHub.
2. Clone o repositório para a sua máquina (`git clone https://github.com/SEU-USUARIO/md-organizer.git`).
3. Crie uma *Branch* para a sua alteração (`git checkout -b feature/minha-melhoria`).
4. Faça o commit das suas alterações (`git commit -m 'feat: adiciona nova funcionalidade incrível'`).
5. Faça o push para a sua branch (`git push origin feature/minha-melhoria`).
6. Abra um *Pull Request* no repositório original descrevendo as mudanças propostas.

## Padrões do Projeto

- **Gerenciador de Dependências**: Utilizamos o `uv` em vez do `pip` puro.
- **Modelos de IA**: Qualquer modificação na lógica de análise deve manter compatibilidade com a API local do `ollama`.
- **Formatação**: Tente manter o padrão estilístico das saídas no terminal (que usam caixas e emojis amigáveis).

Sinta-se livre para abrir *Issues* para discutir grandes mudanças antes de implementar!
