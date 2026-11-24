# Monitoramento IoT VRM — Grupo G01

Projeto integrador de Arquitetura de Computadores: ESP32 + DS18B20 no Wokwi, HTTPS direto, Supabase Edge Function, PostgreSQL e painel estático. O MQTT não é necessário (opção B do enunciado).

## Links e estado verificado

- [Wokwi do grupo](https://wokwi.com/projects/481519064991846401): firmware v6 salvo e sensor verificado em modo local. O código `wokwi/main.py` foi sincronizado com o publicado.
- [Painel GitHub Pages publicado](https://felipestv0.github.io/aula13-iot-g01/): frontend em `docs/index.html`.
- API POST: https://ckccllcmaepeamftkkew.supabase.co/functions/v1/ingest
- API REST GET: https://ckccllcmaepeamftkkew.supabase.co/rest/v1/readings

Em 24/11/2026, um POST autenticado de diagnóstico obteve HTTP 201 e persistiu a mensagem `api-probe-20261124-01` (73 °C). A função temporária de diagnóstico foi desativada. Registros `demo-seed-*` são ensaios SQL. Nenhum dos dois comprova transmissão Wokwi.

## Reprodução

1. Abra o Wokwi do grupo. Substitua integralmente o conteúdo de `main.py` e `diagram.json` pelos arquivos correspondentes desta pasta. Salve e recarregue para conferir. O diagrama define sensor GPIO4, LED amarelo GPIO19 e vermelho GPIO18, resistores e monitor serial.
2. Inicie a simulação. Digite a INGEST_KEY no terminal (somente em uma sessão de execução controlada, sem gravar a digitação), ou pressione Enter vazio para testar apenas o sensor. O segredo não é salvo no código; não compartilhe a saída que mostre o segredo. A chave deve ser a mesma armazenada em Supabase Edge Functions Secrets. As CAs públicas em DER estão incorporadas ao firmware. O TLS valida certificado e hostname. Se a cadeia não corresponder a uma das raízes incluídas, atualize as CAs de confiança; não desative a validação.
3. Em GitHub Settings → Pages, escolha Deploy from a branch → main → /docs → Save. O domínio padrão Supabase não renderiza HTML de Edge Functions, por isso o painel foi migrado para hospedagem estática. O painel utiliza apenas a chave publicável e consulta a API a cada 10 segundos, com timeout de 8 s, recuperação automática e exclusão dos registros de diagnóstico SQL/HTTP.
4. Para reproduzir o backend em outro projeto, execute `supabase/schema.sql`, configure o segredo INGEST_KEY e publique `supabase/functions/ingest/index.ts` com a configuração em `supabase/config.toml`. Atualize URL e chave publicável em `docs/index.html` e host/CA no firmware. A Edge Function dashboard antiga é um artefato legado, não um endereço de entrega.

## Funcionamento

Amostragem nominal a cada 2 s; média móvel de até três leituras; envio a cada 10 s, sujeito ao tempo de conexão/retransmissão. Aviso ≥70 °C (retorno abaixo de 65 °C), crítico ≥90 °C (saída abaixo de 85 °C). O painel indica dados desatualizados após 35 s. O PostgreSQL mantém histórico independente do navegador. RLS ativo: leitura pública apenas de dados simulados, escrita reservada ao backend.

## Validação obrigatória

- Alterar o sensor 25 → 75 → 95 °C; observar média, LEDs e estado.
- Conferir POST 200/201 e ID da mesma mensagem no painel/GET REST.
- Interromper a simulação por mais de 35 s e confirmar desatualização; retomar e confirmar atualização.
- Fechar o painel durante transmissão e conferir histórico após reabrir.
- Registrar o vídeo e as contribuições reais dos integrantes. Não confundir registros de diagnóstico com os produzidos pelo sensor.

Limitações: sensor e temperaturas são simulados; rede e TLS podem introduzir atraso; fila em RAM de uma mensagem pendente, não garante recuperação de todas as amostras após reinício. Nenhum segredo deve ser adicionado ao GitHub ou ao código Wokwi público.

## Auditoria técnica — 24/11/2026

- API corrigida: remoção da autorização QA expirada; validação estrita de `alert`. Função publicada e código sincronizado.
- Teste HTTP real após a correção: 201 para nova leitura de diagnóstico; 200 para repetição; 401 para segredo errado; 400 para temperatura fora da faixa; 400 para alerta enviado como array; 405 para GET. A consulta REST real do painel retornou 200 e oito registros do sensor sem incluir diagnósticos.
- Último registro de sensor confirmado: `438bfd11-8`, média 49,73 °C, recebido em 24/11/2026 às 10:45:10 (Brasília).
- Firmware v6: 13 testes locais de lógica e TLS aprovados; 8 testes locais de API do pacote v6 aprovados. Os testes usam simulações de dependências. Wokwi executado em modo local: `DS18B20 25.0 C | media 25.0 | alerta normal`.
- Painel: sete verificações de atualização com Chromium e respostas REST simuladas, incluindo timeout e recuperação. O código atualizado foi publicado no repositório. A consulta REST com o filtro novo foi validada contra a API real.
- O teste de transmissão da versão v6 não foi concluído porque a automação não conseguiu informar a credencial temporária no monitor serial. Nenhuma leitura QA Wokwi foi recebida nesta execução. A autorização temporária foi revogada. A estabilidade Wi-Fi/TLS e os cenários de interrupção/recuperação ponta a ponta continuam pendentes. Não declarar aprovação final.
