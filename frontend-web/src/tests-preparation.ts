// jsdom n'implemente pas le defilement : sans ce bouchon, chaque navigation
// dans un test remonte une erreur qui n'en est pas une.
import { vi } from 'vitest'

vi.stubGlobal('scrollTo', () => {})
