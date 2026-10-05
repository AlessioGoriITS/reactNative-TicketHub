export function LoadingState({ label = 'Caricamento in corso…' }: { label?: string }) {
  return <div className="feedback loading">{label}</div>
}

export function ErrorState({ message }: { message: string }) {
  return <div className="feedback error" role="alert">{message}</div>
}
