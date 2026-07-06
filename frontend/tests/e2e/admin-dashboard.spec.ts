import { expect, test } from '@playwright/test'

function makeGroup(index: number) {
  return {
    id: `group-${index}`,
    facebook_group_id: String(1000 + index),
    name: `Nhóm kiểm thử ${index}`,
    url: `https://www.facebook.com/groups/${1000 + index}`,
    cover_image_url: null,
    tags: [],
    note: '',
    is_enabled: true,
    is_posting_allowed: index % 2 === 0,
  }
}

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
    await page.route('**/api/groups', async (route) => {
      await route.fulfill({ json: [] })
    })
    await page.route('**/api/automation/group-sync/status', async (route) => {
      await route.fulfill({ json: { status: 'idle', synced_count: 0, message: '' } })
    })
    await page.route('**/api/automation/group-sync/start', async (route) => {
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

  test('trang Nhóm phân trang danh sách và giữ sidebar khi cuộn', async ({ page }) => {
    const groups = Array.from({ length: 25 }, (_, index) => makeGroup(index + 1))
    await page.route('**/api/groups', async (route) => {
      await route.fulfill({ json: groups })
    })
    await page.route('**/api/automation/group-sync/status', async (route) => {
      await route.fulfill({ json: { status: 'idle', synced_count: 0, message: '' } })
    })

    await page.goto('/nhom')

    await expect(page.getByText('Nhóm kiểm thử 1')).toBeVisible()
    await expect(page.getByText('Nhóm kiểm thử 20')).toBeVisible()
    await expect(page.getByText('Nhóm kiểm thử 21')).toBeHidden()
    await expect(page.getByRole('navigation', { name: 'Phân trang nhóm' })).toContainText('Hiển thị 1–20 / 25 nhóm')

    await page.getByRole('link', { name: 'Sau' }).click()

    await expect(page).toHaveURL(/page=2/)
    await expect(page.getByText('Nhóm kiểm thử 21')).toBeVisible()
    await expect(page.getByText('Nhóm kiểm thử 1')).toBeHidden()

    await page.mouse.wheel(0, 1600)
    await expect(page.getByRole('navigation', { name: 'Điều hướng quản trị' }).getByRole('link', { name: /Nhóm/ })).toBeVisible()
  })
})
