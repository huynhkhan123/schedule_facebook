export type SyncStatus =
  | 'idle'
  | 'opening_browser'
  | 'waiting_for_user_scroll'
  | 'syncing_visible_groups'
  | 'needs_user_action'
  | 'stopped'
  | 'error'

export type SyncResponse = {
  status: SyncStatus | string
  synced_count: number
  message?: string
}

export type Group = {
  id: string
  facebook_group_id: string | null
  name: string
  url: string
  cover_image_url: string | null
  tags: string[]
  note: string
  is_enabled: boolean
  is_posting_allowed: boolean
}

export type Connector = {
  id: string
  machine_name: string
  platform: string
  capabilities: string[]
  profile_configured: boolean
  status: string
  last_seen_at: string | null
}

export type PairingCodeResponse = {
  code: string
}
