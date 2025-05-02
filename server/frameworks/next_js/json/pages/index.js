export default function Home() {
    let newObject = {
        message: "Hello World",
        timestamp: new Date().toISOString(),
        randomNumber: Math.floor(Math.random() * 1000),
    };

    return (
        <pre>
      {JSON.stringify(newObject, null, 2)}
    </pre>
    );
}