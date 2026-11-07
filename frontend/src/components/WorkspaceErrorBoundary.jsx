import { Component } from 'react'

export class WorkspaceErrorBoundary extends Component {
  state = { hasError: false }

  static getDerivedStateFromError() { return { hasError: true } }

  componentDidCatch(error, info) {
    console.error('Workspace render error', error, info)
  }

  render() {
    if (!this.state.hasError) return this.props.children
    return <main className="workspace-error" role="alert">
      <section>
        <p>Workspace recovery</p>
        <h1>We could not display this workspace.</h1>
        <span>Reload the page to restore the latest application state. Your data has not been changed.</span>
        <button className="button" onClick={() => window.location.reload()}>Reload workspace</button>
      </section>
    </main>
  }
}
