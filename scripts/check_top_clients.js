const { McpClient } = require('@modelcontextprotocol/client');

async function checkTopClients() {
    const client = new McpClient({
        server: 'supabase',
        accessToken: 'sbp_23167f2e5b6fb4db0ca1521bf8683b5a3cd4f329'
    });

    const query = `
        SELECT nombre, COUNT(*) as cantidad 
        FROM reservas_prod 
        WHERE estado = 'Confirmada' 
        AND fecha >= CURRENT_DATE - INTERVAL '3 months' 
        GROUP BY nombre 
        ORDER BY cantidad DESC 
        LIMIT 5;
    `;

    try {
        const result = await client.query(query);
        console.log('Top 5 clientes con más reservas confirmadas:');
        console.table(result.rows);
    } catch (error) {
        console.error('Error al consultar la base de datos:', error);
    }
}

checkTopClients();
