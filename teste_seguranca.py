
# 1. TESTE DE SECRETS (Para o TruffleHog interceptar)
from psycopg import connection


DATABASE_URL_EXPOSTA = "postgresql://samuel_admin:Rr9XzY4tNq7Wp2Lm@ep-cloud-database.render.com/clinica_medica_segura"


# 2. TESTE DE SAST / SQL INJECTION (Para o Semgrep interceptar)
def buscar_prontuario_vulneravel(request):
    """
    Uma função intencionalmente insegura que concatena parâmetros diretamente na
    query SQL do PostgreSQL, violando os princípios de Security by Design.
    """
    id_paciente = request.GET.get('id')
    
    
    query = f"SELECT * FROM clinica_prontuario WHERE id = {id_paciente};"
    
    with connection.cursor() as cursor:
        cursor.execute(query) 
        row = cursor.fetchone()
        
    return row