### Documentação: Configuração de Expressões Cron na Ferramenta Darwin  
Esta documentação explica como configurar expressões cron para agendamentos na ferramenta Darwin, incluindo sintaxe e o funcionamento do encadeamento de múltiplas expressões cron com lógica **AND**.

---

## 1. Formato Básico da Expressão Cron  
A ferramenta utiliza expressões cron no formato padrão de **5 campos**:  
```plaintext
┌───────────── minuto (0 - 59)  
│ ┌───────────── hora (0 - 23)  
│ │ ┌───────────── dia do mês (1 - 31) [suporta 'W' para dias úteis]  
│ │ │ ┌───────────── mês (1 - 12)  
│ │ │ │ ┌───────────── dia da semana (0 - 6, 0 = Domingo)  
│ │ │ │ │  
* * * * *  
```

### Exemplos Válidos:  
- `0 9 * * 1-5`: Dias úteis (segunda a sexta) às 09:00.  
- `0 0 3W * *`: 3º dia útil do mês à meia-noite.  
- `30 18 1,15 * *`: Dias 1 e 15 de cada mês às 18:30.  

---

## 2. Modificador `W` (Dias Úteis)  
O modificador `W` filtra **dias úteis**, excluindo fins de semana (sábado e domingo) e feriados configurados.  

### Sintaxe:  
- `nW`: Representa o **n-ésimo dia útil** do mês.  
  - Exemplo: `5W` = 5º dia útil do mês.  
- `*W`: Corresponde a qualquer dia útil (equivalente a `1W-31W`, mas apenas dias válidos).  

### Regras:  
1. **Feriados**: Datas na lista `holidays` são ignoradas.  
2. **Cálculo**: Dias úteis são contados sequencialmente, pulando fins de semana e feriados.  
3. **Compatibilidade**: Não combine `W` com intervalos (ex: `1-5W`). Use `1W,2W,3W,4W,5W`.  

#### Exemplo:  
- **Expressão**: `0 8 3W * *`  
- **Funcionamento**: Às 08:00 do 3º dia útil do mês (ex: se os dias 1 e 2 forem feriados, o 3º dia útil será o dia 6).  

---

## 3. Encadeamento de Expressões Cron (Lógica **AND**)  
Para cenários complexos, é possível combinar múltiplas expressões cron. A data resultante deve satisfazer **todas as expressões simultaneamente**.  

### Funcionamento:  
- **Entrada**: Lista de expressões cron.  
- **Saída**: Datas que atendem **a todas as condições ao mesmo tempo**.  

### Exemplo 1:  
```python  
# Expressões:  
expr1 = "0 9 15W * *"   # 15º dia útil do mês às 09:00  
expr2 = "0 9 * * 3"     # Toda quarta-feira às 09:00  

# Resultado:  
# Datas que são:  
# - 15º dia útil do mês  
# - Quarta-feira  
# - Horário: 09:00  
```  

### Exemplo 2:  
```python  
# Expressões:  
expr1 = "0 12 * 3 *"    # Todos os dias de março ao meio-dia  
expr2 = "0 12 10W * *"  # 10º dia útil do mês ao meio-dia  

# Resultado:  
# 10º dia útil de março, ao meio-dia.  
```  

---

## 4. Regras de Compatibilidade  
1. **Campos de Tempo**:  
   - Horas e minutos devem ser iguais em todas as expressões para haver correspondência.  
   - Exemplo: `0 9 * * *` e `0 12 * * *` → **Sem correspondência** (horários diferentes).  

2. **Dias do Mês vs. Dias da Semana**:  
   - O encadeamento usa lógica **AND**. Exemplo: `["0 9 5 * *", "0 9 * * 1"]` → Datas que são **dia 5 do mês e segunda-feira**.  

3. **Limitações**:  
   - Evite combinar `W` com dias fixos (ex: `5W,10`). Prefira expressões separadas.  

---

## 5. Casos de Uso  
| Descrição                     | Expressões Cron                          | Comportamento                                                                 |  
|-------------------------------|------------------------------------------|-------------------------------------------------------------------------------|  
| **Folha de pagamento**         | `["0 8 5W * *", "0 8 * * 5"]`            | 5º dia útil do mês **que também é sexta-feira**, às 08:00.                    |  
| **Backup mensal**              | `["0 2 1W * *"]`                         | 1º dia útil do mês às 02:00.                                                  |  
| **Relatório trimestral**       | `["0 10 15W 1,4,7,10 *"]`                | 15º dia útil de janeiro, abril, julho e outubro às 10:00.                     |  

---

## 6. Perguntas Frequentes (FAQ)  

### Q1: Como funcionam feriados com múltiplas expressões?  
- Feriados afetam **todas as expressões** que usam `W`. Se uma data for feriado, ela será ignorada em todas as condições.  

### Q2: Posso misturar `W` com dias normais em uma única expressão?  
- Sim! Exemplo: `0 9 3W,15 * *` → 3º dia útil **ou** dia 15 do mês às 09:00.  
- **Observação**: Em múltiplas expressões, use `AND`. Para `OR`, utilize uma única expressão com vírgulas.  

### Q3: O que acontece se as expressões forem conflitantes?  
- Nenhuma data será encontrada, e um erro `RuntimeError` será levantado após 1500 iterações.  

### Q4: Como definir horários específicos com `W`?  
- Use os campos de hora/minuto normalmente. Exemplo: `30 18 2W * *` → 2º dia útil do mês às 18:30.  

---

## 7. Conclusão  
O encadeamento de expressões cron no Darwin permite criar regras complexas com lógica **AND**, ideal para automações que exigem múltiplas condições simultâneas. Use `W` para dias úteis e combine expressões para cenários como relatórios mensais, pagamentos ou backups estratégicos.  

Para dúvidas, consulte a equipe de suporte ou a documentação técnica avançada.  























### Documentação: Configuração de Expressões Cron na Ferramenta Darwin  
Esta documentação explica como configurar expressões cron para agendamentos na ferramenta Darwin, incluindo sintaxe e o funcionamento do encadeamento de múltiplas expressões cron com lógica **AND**.

---

## 1. Formato Básico da Expressão Cron  
A ferramenta utiliza expressões cron no formato padrão de **5 campos**:  
```plaintext
┌───────────── minuto (0 - 59)  
│ ┌───────────── hora (0 - 23)  
│ │ ┌───────────── dia do mês (1 - 31) [suporta 'W' para dias úteis]  
│ │ │ ┌───────────── mês (1 - 12)  
│ │ │ │ ┌───────────── dia da semana (0 - 6, 0 = Domingo)  
│ │ │ │ │  
* * * * *  
```

### Exemplos Válidos:  
- `0 9 * * 1-5`: Dias úteis (segunda a sexta) às 09:00.  
- `0 0 3W * *`: 3º dia útil do mês à meia-noite.  
- `30 18 1,15 * *`: Dias 1 e 15 de cada mês às 18:30.  

---

## 2. Modificador `W` (Dias Úteis)  
O modificador `W` filtra **dias úteis**, excluindo fins de semana (sábado e domingo) e feriados configurados.

### Sintaxe:  
- **`nW`**: Representa o **n-ésimo dia útil** do mês.  
  - *Exemplo*: `5W` = 5º dia útil do mês.  
- **`*W`**: Corresponde a qualquer dia útil dentro do intervalo válido (interpreta-se como todos os dias possíveis, mas efetivamente somente os dias úteis são considerados).

### Regras:  
1. **Feriados**:  
   - Datas especificadas na lista de `holidays` são ignoradas, garantindo que o dia retornado seja efetivamente um dia útil.
2. **Cálculo dos Dias Úteis**:  
   - Os dias úteis são contados sequencialmente, pulando fins de semana e feriados.  
   - Caso a data indicada originalmente seja um feriado ou um fim de semana, o mecanismo ajusta para o próximo dia útil conforme a contagem.
3. **Compatibilidade com Outros Valores**:  
   - É possível combinar o modificador `W` com números fixos em uma única expressão.  
   - **Importante**: Não combine `W` com intervalos (ex: `1-5W`). Se necessário, liste-os separadamente (ex: `1W,2W,3W,4W,5W`).

#### Exemplo:  
- **Expressão**: `0 8 3W * *`  
- **Funcionamento**: Às 08:00 do 3º dia útil do mês.  
  - Se os dias 1 e 2 forem feriados ou caírem em um fim de semana, o sistema avançará até identificar o 3º dia útil (por exemplo, dia 6).

---

## 3. Encadeamento de Expressões Cron (Lógica **AND**)  
Para cenários complexos, é possível combinar múltiplas expressões cron. Neste encadeamento, a data resultante deve satisfazer **todas as expressões simultaneamente**.

### Funcionamento:  
- **Entrada**: Uma lista de expressões cron que devem ser aplicadas em conjunto.  
- **Saída**: Datas que atendem **todas as condições** estabelecidas pelas expressões.  
- **Condição de Horário**:  
  - Os campos de hora e minuto **devem ser idênticos** em todas as expressões para que haja correspondência.  
  - Caso os horários sejam diferentes, não haverá interseção e, consequentemente, nenhuma data será considerada válida.

### Exemplos:

#### Exemplo 1:  
```python
# Expressões:  
expr1 = "0 9 15W * *"   # 15º dia útil do mês às 09:00  
expr2 = "0 9 * * 3"     # Toda quarta-feira às 09:00  

# Resultado:  
# Datas que são:
# - 15º dia útil do mês  
# - Quarta-feira  
# - Horário: 09:00  
```

#### Exemplo 2:  
```python
# Expressões:  
expr1 = "0 12 * 3 *"    # Todos os dias de março ao meio-dia  
expr2 = "0 12 10W * *"  # 10º dia útil do mês ao meio-dia  

# Resultado:  
# 10º dia útil de março, ao meio-dia.
```

#### Exemplo 3:  
```python
# Expressões:  
expr1 = "0 9 5 * *"    # Dia 5 do mês às 09:00  
expr2 = "0 9 * * 1"    # Toda segunda-feira às 09:00  

# Resultado:  
# Datas que são dia 5 do mês E segunda-feira
```

---

## 4. Combinação de Dias do Mês com Dias da Semana  
- Ao combinar expressões que definem **dias do mês** com expressões que definem **dias da semana**, a data final deve cumprir ambas as condições simultaneamente.
- **Exemplo**:  
  - `"0 9 5 * *", "0 9 * * 1"`  
  - Apenas datas que sejam o dia 5 do mês **e** uma segunda-feira serão consideradas.

---

## 5. Regras de Compatibilidade e Limitações  
1. **Campos de Tempo**:  
   - Os campos de hora e minuto devem ser iguais em todas as expressões para que a interseção seja válida.  
   - Exemplo: `"0 9 * * *"` e `"0 12 * * *"` → **Sem correspondência** (horários diferentes).
2. **Dias do Mês vs. Dias da Semana**:  
   - O encadeamento utiliza a lógica **AND**.  
   - Exemplo: `"0 9 5 * *", "0 9 * * 1"` → Apenas datas que sejam **dia 5 do mês e segunda-feira**.
3. **Combinação com o Modificador `W`**:  
   - Embora seja possível misturar `W` com dias fixos dentro de uma mesma expressão (ex: `"0 9 3W,15 * *"`), em cenários com múltiplas expressões, recomenda-se o uso do encadeamento com lógica **AND** para evitar ambiguidades.
4. **Limite de Iterações**:  
   - Se as expressões forem conflitantes, o sistema tentará encontrar uma data válida até um máximo de 1500 iterações, após o que um erro será gerado.

---

## 6. Conclusão  
O encadeamento de expressões cron na ferramenta Darwin permite criar regras complexas com lógica **AND**, ideal para automações estratégicas. Use o modificador `W` para garantir agendamentos em dias úteis e combine expressões para cenários como relatórios mensais, pagamentos ou backups estratégicos.
