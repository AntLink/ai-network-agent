import { Construction } from 'lucide-react'
import { Card, CardContent } from 'src/components/ui/card'

type PlaceholderPageProps = {
  title: string
  description: string
}

const PlaceholderPage = ({ title, description }: PlaceholderPageProps) => (
  <div className="grid gap-4">
    <div>
      <h1 className="text-2xl font-semibold tracking-normal">{title}</h1>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
    <Card>
      <CardContent className="flex min-h-72 items-center justify-center">
        <div className="max-w-md text-center">
          <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-lg bg-muted text-muted-foreground">
            <Construction className="size-6" />
          </div>
          <h2 className="text-base font-semibold">Prepared for next phase</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Route, layout, loading/error conventions, and navigation are ready. Feature workflows will be wired phase by phase.
          </p>
        </div>
      </CardContent>
    </Card>
  </div>
)

export default PlaceholderPage
