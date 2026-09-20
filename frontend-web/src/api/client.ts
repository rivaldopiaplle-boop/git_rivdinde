// Le seul endroit du front qui parle a l'API.
//
// Tout passe par ici : le jeton, la cle de panier, le format d'erreur, l'URL
// de base. Le jour ou l'un des quatre change, un seul fichier bouge — et aucun
// ecran n'a besoin de savoir qu'un jeton existe.

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export type ErreurApi = {
  code: string
  message: string
  details: Record<string, string[]>
}

export class EchecApi extends Error {
  constructor(
    public statut: number,
    public erreur: ErreurApi,
  ) {
    super(erreur.message)
  }
}

let jetonAcces: string | null = null
let cleSession: string | null = null

export function poserJeton(jeton: string | null) {
  jetonAcces = jeton
}

/** La cle qui identifie le panier d'un visiteur sans compte (D-03). */
export function poserCleSession(cle: string | null) {
  cleSession = cle
}

async function appeler<T>(chemin: string, options: RequestInit = {}): Promise<T> {
  let reponse: Response
  try {
    reponse = await fetch(`${BASE}${chemin}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(jetonAcces ? { Authorization: `Bearer ${jetonAcces}` } : {}),
        ...(cleSession ? { 'X-Panier-Session': cleSession } : {}),
        ...options.headers,
      },
    })
  } catch {
    // Le serveur n'a pas repondu du tout : on le dit en francais, pas par un
    // « TypeError: Failed to fetch » que personne ne peut interpreter.
    throw new EchecApi(0, {
      code: 'reseau',
      message: "L'API ne repond pas. Est-elle demarree ?",
      details: {},
    })
  }

  if (reponse.status === 204) return undefined as T

  const corps = await reponse.json().catch(() => null)

  if (!reponse.ok) {
    const erreur: ErreurApi = corps?.erreur ?? {
      code: 'inconnue',
      message: `Erreur ${reponse.status}.`,
      details: {},
    }
    throw new EchecApi(reponse.status, erreur)
  }

  // L'API enveloppe toujours ses reponses dans { data: ... } (contrat-api.md).
  return (corps?.data ?? corps) as T
}

/** Le corps complet, quand on a besoin de `meta` en plus de `data`. */
export async function appelerComplet<T>(chemin: string): Promise<T> {
  const reponse = await fetch(`${BASE}${chemin}`, {
    headers: {
      ...(jetonAcces ? { Authorization: `Bearer ${jetonAcces}` } : {}),
      ...(cleSession ? { 'X-Panier-Session': cleSession } : {}),
    },
  }).catch(() => null)

  if (!reponse || !reponse.ok) {
    throw new EchecApi(reponse?.status ?? 0, {
      code: 'reseau',
      message: "L'API ne repond pas.",
      details: {},
    })
  }
  return (await reponse.json()) as T
}

export const api = {
  get: <T>(chemin: string) => appeler<T>(chemin),
  post: <T>(chemin: string, corps?: unknown) =>
    appeler<T>(chemin, { method: 'POST', body: JSON.stringify(corps ?? {}) }),
  patch: <T>(chemin: string, corps: unknown) =>
    appeler<T>(chemin, { method: 'PATCH', body: JSON.stringify(corps) }),
  supprimer: <T>(chemin: string) => appeler<T>(chemin, { method: 'DELETE' }),
}
