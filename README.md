# Monitoramento IoT VRM — Grupo G01

Projeto integrador de Arquitetura de Computadores. Monitoramento de temperatura simulada com ESP32, DS18B20, API REST HTTPS e PostgreSQL no Supabase.

- [Simulação Wokwi](https://wokwi.com/projects/481519064991846401)
- [Painel web](https://ckccllcmaepeamftkkew.supabase.co/functions/v1/dashboard)
- API: `POST /functions/v1/ingest` e `GET /rest/v1/readings`.

A comunicação MQTT foi substituída por HTTPS direto (opção B do enunciado). Os dados são sintéticos. A validação de ponta a ponta precisa de execução do firmware com credenciais privadas; registros `demo-seed-*` são ensaios do banco, não transmissões do sensor.

Nunca publique a INGEST_KEY. Consulte os arquivos de configuração de exemplo e as instruções do firmware.
