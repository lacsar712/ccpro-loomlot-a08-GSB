<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { user } from '../lib/auth.js';

  $: isAdmin = $user?.role === 'admin';

  let houses = [];
  let rows = [];
  let error = '';
  let form = {
    dyeHouseId: '',
    recipeName: '',
    versionNo: 1,
    maxFabricKg: 50,
    isActive: true,
  };
  let editing = null;

  async function load() {
    error = '';
    try {
      [houses, rows] = await Promise.all([api('/dye-houses'), api('/recipe-versions')]);
      if (!form.dyeHouseId && houses.length) form.dyeHouseId = String(houses[0].id);
    } catch (e) {
      error = e.message;
    }
  }

  onMount(load);

  $: activeCount = rows.filter((r) => r.isActive).length;

  function houseName(id) {
    return houses.find((h) => h.id === id)?.name || id;
  }

  async function save() {
    error = '';
    try {
      if (editing) {
        const body = {
          recipeName: form.recipeName.trim(),
          versionNo: Number(form.versionNo),
          maxFabricKg: Number(form.maxFabricKg),
          isActive: form.isActive,
        };
        await api(`/recipe-versions/${editing}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        const body = {
          dyeHouseId: Number(form.dyeHouseId),
          recipeName: form.recipeName.trim(),
          versionNo: Number(form.versionNo),
          maxFabricKg: Number(form.maxFabricKg),
          isActive: form.isActive,
        };
        await api('/recipe-versions', { method: 'POST', body: JSON.stringify(body) });
      }
      editing = null;
      form = {
        dyeHouseId: form.dyeHouseId,
        recipeName: '',
        versionNo: 1,
        maxFabricKg: 50,
        isActive: true,
      };
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  function startEdit(row) {
    editing = row.id;
    form = {
      dyeHouseId: String(row.dyeHouseId),
      recipeName: row.recipeName,
      versionNo: row.versionNo,
      maxFabricKg: row.maxFabricKg,
      isActive: row.isActive,
    };
  }

  async function toggle(row) {
    error = '';
    try {
      await api(`/recipe-versions/${row.id}`, {
        method: 'PUT',
        body: JSON.stringify({ isActive: !row.isActive }),
      });
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function remove(id) {
    if (!confirm('确认删除该配方版本？历史染程仍保留原配方名。')) return;
    error = '';
    try {
      await api(`/recipe-versions/${id}`, { method: 'DELETE' });
      await load();
    } catch (e) {
      error = e.message;
    }
  }
</script>

<h1 class="page-title">配方版本</h1>
<p class="page-sub">
  染程开立须命中所属染坊的启用版本，且布重不超过该版本单次上限；停用版本不可再被新染程引用。
</p>

{#if isAdmin}
  <div class="panel" style="margin-bottom:1rem;">
    <div class="form-grid">
      <label
        >所属染坊
        <select bind:value={form.dyeHouseId} disabled={!!editing}>
          {#each houses as h}
            <option value={String(h.id)}>{h.name}</option>
          {/each}
        </select>
      </label>
      <label>配方名 <input bind:value={form.recipeName} /></label>
      <label>版本号 <input type="number" step="1" min="1" bind:value={form.versionNo} /></label>
      <label
        >单次布重上限 kg <input type="number" step="0.1" min="0.1" bind:value={form.maxFabricKg} /></label
      >
      <label
        >是否启用
        <select bind:value={form.isActive}>
          <option value={true}>启用</option>
          <option value={false}>停用</option>
        </select>
      </label>
    </div>
    <div class="toolbar">
      <button class="btn" type="button" on:click={save}>{editing ? '保存修改' : '新建版本'}</button>
      {#if editing}
        <button class="btn ghost" type="button" on:click={() => (editing = null)}>取消</button>
      {/if}
    </div>
    {#if error}<p class="err">{error}</p>{/if}
  </div>
{:else}
  <p class="page-sub">当前为操作员账号，版本列表只读；开染程时将受启用版本与布重上限约束。</p>
  {#if error}<p class="err">{error}</p>{/if}
{/if}

<div class="panel">
  <p class="hint-line">启用 {activeCount} 条 / 共 {rows.length} 条（与总览看板「启用配方版本」一致）</p>
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>染坊</th>
        <th>配方名</th>
        <th>版本号</th>
        <th>状态</th>
        <th>上限 kg</th>
        {#if isAdmin}<th></th>{/if}
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        <tr>
          <td>{row.id}</td>
          <td>{houseName(row.dyeHouseId)}</td>
          <td>{row.recipeName}</td>
          <td>v{row.versionNo}</td>
          <td><span class="badge {row.isActive ? 'on' : 'off'}">{row.isActive ? '启用' : '停用'}</span></td>
          <td>{row.maxFabricKg}</td>
          {#if isAdmin}
            <td class="row-actions">
              <button class="btn ghost small" type="button" on:click={() => toggle(row)}
                >{row.isActive ? '停用' : '启用'}</button
              >
              <button class="btn ghost small" type="button" on:click={() => startEdit(row)}>编辑</button>
              <button class="btn danger small" type="button" on:click={() => remove(row.id)}>删除</button>
            </td>
          {/if}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
