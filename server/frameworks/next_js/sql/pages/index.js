import { Pool } from 'pg';

export async function getServerSideProps() {
    const pool = new Pool({
        connectionString: process.env.DATABASE_URL,
    });

    const { rows } = await pool.query('SELECT * FROM sample_data');
    await pool.end();

    return {
        props: {
            data: rows,
        },
    };
}

export default function Home({ data }) {
    return (
        <div>
            <h1>Sample Data from Postgres:</h1>
            <ul>
                {data.map((row) => (
                    <li key={row.id}>{row.title}</li>
                ))}
            </ul>
        </div>
    );
}
