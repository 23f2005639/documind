import { useState } from "react"

export default function Chatbot() {
  const [query, setQuery] = useState("")

  async function askQuestion() {
    console.log("Searching:", query)
  }

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <button onClick={askQuestion}>
        Ask AI
      </button>
    </div>
  )
}