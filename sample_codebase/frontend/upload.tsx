export default function UploadPage() {
  async function uploadFile() {
    console.log("Uploading file...")
  }

  return (
    <div>
      <button onClick={uploadFile}>
        Upload Document
      </button>
    </div>
  )
}