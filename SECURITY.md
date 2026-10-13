# Política de segurança

## Versões suportadas

Somente a versão mais recente (última GitHub Release) recebe correções de segurança.

## Como relatar uma vulnerabilidade

**Não abra uma issue pública.** Use o relato privado do GitHub:
aba **Security → Report a vulnerability** (ative em *Settings → Code security →
Private vulnerability reporting*).

Inclua: descrição, passos para reproduzir, impacto e versão afetada.
Compromisso de resposta: confirmação em até 3 dias úteis; correção de falhas
críticas em até 7 dias.

## Dados pessoais (LGPD)

Este sistema trabalha com indicadores **agregados por curso**. Não registre dados
pessoais de estudantes ou docentes (nome, CPF, matrícula) em medições, logs,
issues ou métricas. Indicadores com turmas muito pequenas podem permitir
reidentificação: avalie agregar ou suprimir valores com poucos estudantes.

## Controles automatizados neste repositório

| Controle | Onde |
|---|---|
| Segredos bloqueados antes do commit | `.pre-commit-config.yaml` (gitleaks) |
| SAST (código e workflows) | `.github/workflows/security.yml` (CodeQL) |
| CVEs em dependências | Dependabot, pip-audit, dependency-review |
| Imagem de container | Trivy, Hadolint, usuário não-root |
| IaC e Kubernetes | Checkov, Trivy, Kyverno |
| Cadeia de suprimentos | Actions fixadas por SHA, SBOM, Cosign, proveniência SLSA |
| Postura do repositório | OpenSSF Scorecard |
| Aplicação em execução | OWASP ZAP (DAST) |
