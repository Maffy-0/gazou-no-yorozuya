import { useState, type ChangeEvent } from 'react'
import './App.css'

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [compressedImageUrl, setCompressedImageUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0] ?? null

    setFile(selectedFile)
    setCompressedImageUrl((currentUrl) => {
      if (currentUrl) {
        URL.revokeObjectURL(currentUrl)
      }

      return ''
    })
  }

  const handleCompress = async () => {
    if (!file) {
      return
    }

    setIsLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:8000/api/compress', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('画像の圧縮に失敗しました')
      }

      const blob = await response.blob()
      const imageUrl = URL.createObjectURL(blob)

      setCompressedImageUrl((currentUrl) => {
        if (currentUrl) {
          URL.revokeObjectURL(currentUrl)
        }

        return imageUrl
      })
    } catch (error) {
      console.error(error)
      alert('画像の圧縮に失敗しました。バックエンドの起動状態を確認してください。')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main>
      <h1>画像圧縮テスト</h1>

      <input type="file" accept="image/*" onChange={handleFileChange} />

      <button type="button" onClick={handleCompress} disabled={!file || isLoading}>
        {isLoading ? '通信中...' : '圧縮する'}
      </button>

      {compressedImageUrl && (
        <img src={compressedImageUrl} alt="圧縮後の画像" />
      )}
    </main>
  )
}

export default App
