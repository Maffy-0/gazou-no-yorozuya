import { useState, type ChangeEvent } from 'react'
import './App.css'

type ResolutionPreset = 'original' | 'medium' | 'small'
type QualityPreset = 'high' | 'medium' | 'low'

type ImageInfo = {
  fileName?: string
  format: string
  mimeType: string
  width: number
  height: number
  mode: string
  bytes: number
}

type CompressResult = {
  imageBase64: string
  mimeType: string
  downloadFileName: string
  compression: {
    originalBytes: number
    compressedBytes: number
    reductionRate: number
  }
  before: ImageInfo
  after: ImageInfo
}

const resolutionOptions: Array<{
  value: ResolutionPreset
  label: string
  description: string
}> = [
  { value: 'original', label: '原寸', description: '元画像の解像度を維持' },
  { value: 'medium', label: '中', description: '長辺を最大1280pxに縮小' },
  { value: 'small', label: '小', description: '長辺を最大640pxに縮小' },
]

const qualityOptions: Array<{
  value: QualityPreset
  label: string
  description: string
}> = [
  { value: 'high', label: '高', description: 'q80' },
  { value: 'medium', label: '中', description: 'q60' },
  { value: 'low', label: '低', description: 'q40' },
]

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [resolution, setResolution] = useState<ResolutionPreset>('medium')
  const [quality, setQuality] = useState<QualityPreset>('medium')
  const [result, setResult] = useState<CompressResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const imageSrc = result
    ? `data:${result.mimeType};base64,${result.imageBase64}`
    : ''

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0] ?? null

    setFile(selectedFile)
    setResult(null)
    setErrorMessage('')
  }

  const handleCompress = async () => {
    if (!file) {
      return
    }

    setIsLoading(true)
    setErrorMessage('')
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('resolution', resolution)
      formData.append('quality', quality)

      const response = await fetch('http://localhost:8000/api/compress', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        const detail =
          typeof errorData?.detail === 'string'
            ? errorData.detail
            : '画像の圧縮に失敗しました。'
        throw new Error(detail)
      }

      const responseData = (await response.json()) as CompressResult
      setResult(responseData)
    } catch (error) {
      console.error(error)
      setErrorMessage(
        error instanceof Error
          ? error.message
          : '画像の圧縮に失敗しました。バックエンドの起動状態を確認してください。',
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = () => {
    if (!result) {
      return
    }

    const binaryString = atob(result.imageBase64)
    const bytes = new Uint8Array(binaryString.length)

    for (let index = 0; index < binaryString.length; index += 1) {
      bytes[index] = binaryString.charCodeAt(index)
    }

    const blob = new Blob([bytes], { type: result.mimeType })
    const downloadUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = result.downloadFileName
    link.click()
    URL.revokeObjectURL(downloadUrl)
  }

  return (
    <main className="app-shell">
      <section className="intro">
        <p className="eyebrow">Gazou no Yorozuya</p>
        <h1>画像圧縮</h1>
        <p className="lead">
          JPEG / PNG / WebP の画像を、解像度と品質を選んで軽量化します。
        </p>
      </section>

      <section className="workspace" aria-label="画像圧縮フォーム">
        <div className="control-area">
          <label className="file-picker">
            <span>画像ファイル</span>
            <input type="file" accept="image/*" onChange={handleFileChange} />
          </label>

          <fieldset>
            <legend>解像度</legend>
            <div className="option-grid">
              {resolutionOptions.map((option) => (
                <label key={option.value} className="option">
                  <input
                    type="radio"
                    name="resolution"
                    value={option.value}
                    checked={resolution === option.value}
                    onChange={() => setResolution(option.value)}
                  />
                  <span>{option.label}</span>
                  <small>{option.description}</small>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend>品質</legend>
            <div className="option-grid">
              {qualityOptions.map((option) => (
                <label key={option.value} className="option">
                  <input
                    type="radio"
                    name="quality"
                    value={option.value}
                    checked={quality === option.value}
                    onChange={() => setQuality(option.value)}
                  />
                  <span>{option.label}</span>
                  <small>{option.description}</small>
                </label>
              ))}
            </div>
          </fieldset>

          <button
            type="button"
            className="primary-button"
            onClick={handleCompress}
            disabled={!file || isLoading}
          >
            {isLoading ? '圧縮中...' : '圧縮する'}
          </button>

          {errorMessage && <p className="error-message">{errorMessage}</p>}
        </div>

        <div className="result-area" aria-live="polite">
          {result ? (
            <>
              <div className="preview-frame">
                <img src={imageSrc} alt="圧縮後の画像" />
              </div>

              <div className="result-summary">
                <p>{buildCompressionMessage(result)}</p>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleDownload}
                >
                  ダウンロード
                </button>
              </div>

              <div className="info-grid">
                <ImageInfoPanel title="変換前" info={result.before} />
                <ImageInfoPanel title="変換後" info={result.after} />
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p>圧縮後の画像と情報がここに表示されます。</p>
            </div>
          )}
        </div>
      </section>
    </main>
  )
}

function ImageInfoPanel({ title, info }: { title: string; info: ImageInfo }) {
  return (
    <section className="info-panel">
      <h2>{title}</h2>
      <dl>
        {info.fileName && (
          <>
            <dt>ファイル名</dt>
            <dd>{info.fileName}</dd>
          </>
        )}
        <dt>形式</dt>
        <dd>{info.format}</dd>
        <dt>MIME</dt>
        <dd>{info.mimeType}</dd>
        <dt>解像度</dt>
        <dd>
          {info.width} x {info.height}px
        </dd>
        <dt>モード</dt>
        <dd>{info.mode}</dd>
        <dt>容量</dt>
        <dd>{formatBytes(info.bytes)}</dd>
      </dl>
    </section>
  )
}

function buildCompressionMessage(result: CompressResult) {
  const { originalBytes, compressedBytes, reductionRate } = result.compression
  const before = formatBytes(originalBytes)
  const after = formatBytes(compressedBytes)

  if (reductionRate >= 0) {
    return `${reductionRate.toFixed(1)}% の圧縮に成功（${before} → ${after}）`
  }

  return `容量が ${Math.abs(reductionRate).toFixed(1)}% 増加しました（${before} → ${after}）`
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`
  }

  const megabytes = bytes / 1024 / 1024
  if (megabytes >= 1) {
    return `${megabytes.toFixed(2)} MB`
  }

  return `${(bytes / 1024).toFixed(1)} KB`
}

export default App
