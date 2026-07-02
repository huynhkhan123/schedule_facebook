import { expect, test } from '@playwright/test'

test.describe('dashboard admin tiếng Việt', () => {
  test('hiển thị shell quản trị dark-first theo Octo Code', async ({ page }) => {
    await page.goto('/')

    await expect(page.getByRole('navigation', { name: 'Điều hướng quản trị' }).getByRole('link', { name: /Tổng quan/ })).toBeVisible()
    await expect(page.getByRole('navigation', { name: 'Điều hướng quản trị' }).getByRole('link', { name: /Nhóm/ })).toBeVisible()
    await expect(page.getByRole('navigation', { name: 'Điều hướng quản trị' }).getByRole('link', { name: /Bài viết/ })).toBeVisible()
    await expect(page.getByRole('navigation', { name: 'Điều hướng quản trị' }).getByRole('link', { name: /Chiến dịch/ })).toBeVisible()
    await expect(page.getByRole('navigation', { name: 'Điều hướng quản trị' }).getByRole('link', { name: /Nhật ký/ })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Tổng quan vận hành' })).toBeVisible()
    await expect(page.getByText('Giới hạn an toàn')).toBeVisible()

    await expect(page.locator('html')).toHaveCSS('background-color', 'rgb(13, 17, 23)')
  })

  test('trang Nhóm có controls đồng bộ tiếng Việt và empty state', async ({ page }) => {
    await page.route('**/api/backend/groups', async (route) => {
      await route.fulfill({ json: [] })
    })
    await page.route('**/api/backend/automation/group-sync/status', async (route) => {
      await route.fulfill({ json: { status: 'idle', synced_count: 0, message: '' } })
    })
    await page.route('**/api/backend/automation/group-sync/start', async (route) => {
      await route.fulfill({ json: { status: 'waiting_for_user_scroll', synced_count: 0, message: '' } })
    })

    await page.goto('/nhom')

    await expect(page.getByRole('heading', { name: 'Quản lý nhóm' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Bắt đầu đồng bộ' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Thu thập nhóm đang hiển thị' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Dừng đồng bộ' })).toBeVisible()
    await expect(page.getByText('Chưa có nhóm nào được đồng bộ')).toBeVisible()

    await page.getByRole('button', { name: 'Bắt đầu đồng bộ' }).click()

    await expect(page.getByText('Chờ bạn cuộn trang nhóm').first()).toBeVisible()
  })
})
