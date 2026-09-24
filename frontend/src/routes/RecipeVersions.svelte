<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { isSupervisor } from '../lib/auth.js';

  let rows = [];
  let houses = [];
  let error = '';
  let form = {
    dyeHouseId: '',
    recipeName: '',
    versionNo: 1,
    isActive: true,
    fabricKgMax: 50,
  };
  let editing = null;

  async function load() {
    error = '';
    try {
      [rows, houses] = await Promise.all([api('/recipe-versions'), api('/dye-houses')]);
      if (!form.dyeHouseId && houses.length) form.dyeHouseId = String(houses[0].id);
    } catch (e) {
      error = e.message;
    }
  }

  onMount(load);

  function houseName(id) {
    const h = houses.find((x) => x.id === id);
    return h ? h.name : id;
  }

  async function save() {
    error = '';
    try {
      const body = {
        dyeHouseId: Number(form.dyeHouseId),
        recipeName: form.recipeName.trim(),
        versionNo: Number(form.versionNo),
        isActive: !!form.isActive,
        fabricKgMax: Number(form.fabricKgMax),
      };
      if (editing) {
        await api(`/recipe-versions/${editing}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await api('/recipe-versions', { method: 'POST', body: JSON.stringify(body) });
      }
      resetForm();
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  function resetForm() {
    editing = null;
    form = {
      dyeHouseId: houses.length ? String(houses[0].id) : '',
      recipeName: '',
      versionNo: 1,
      isActive: true,
      fabricKgMax: 50,
    };
  }

  function startEdit(row) {
    editing = row.id;
    form = {
      dyeHouseId: String(row.dyeHouseId),
      recipeName: row.recipeName,
      versionNo: row.versionNo,
      isActive: row.isActive,
      fabricKgMax: row.fabricKgMax,
    };
  }

  async function setActive(id, active) {
    error = '';
    try {
      await api(`/recipe-versions/${id}/${active ? 'enable' : 'disable'}`, { method: 'POST' });
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function remove(id) {
    if (!confirm('确认删除该配方版本？')) return;
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
  版本挂在染坊下，同坊同配方名下版本号唯一；仅启用版本可用于开立染程，并受单次布重上限约束。
  {$isSupervisor ? '' : '当前为操作员账号，版本只读，启停与维护请联系主管。'}
</p>

{#if $isSupervisor}
  <div class="panel" style="margin-bottom:1rem;">
    <div class="form-grid">
      <label
        >所属染坊
        <select bind:value={form.dyeHouseId}>
          {#each houses as h}
            <option value={String(h.id)}>{h.name}</option>
          {/each}
        </select>
      </label>
      <label>配方名 <input bind:value={form.recipeName} /></label>
      <label>版本号 <input type="number" min="1" step="1" bind:value={form.versionNo} /></label>
      <label
        >单次布重上限 kg
        <input type="number" min="0.1" step="0.1" bind:value={form.fabricKgMax}
      /></label>
      <label class="check-label">
        <input type="checkbox" bind:checked={form.isActive} />
        启用
      </label>
    </div>
    <div class="toolbar">
      <button class="btn" type="button" on:click={save}
        >{editing ? '保存修改' : '新建版本'}</button
      >
      {#if editing}
        <button class="btn ghost" type="button" on:click={resetForm}>取消</button>
      {/if}
    </div>
    {#if error}<p class="err">{error}</p>{/if}
  </div>
{/if}

<div class="panel">
  {#if !$isSupervisor && error}<p class="err">{error}</p>{/if}
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>所属染坊</th>
        <th>配方名</th>
        <th>版本号</th>
        <th>状态</th>
        <th>单次布重上限 kg</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        <tr>
          <td>{row.id}</td>
          <td>{houseName(row.dyeHouseId)}</td>
          <td>{row.recipeName}</td>
          <td>v{row.versionNo}</td>
          <td>
            <span class="badge {row.isActive ? 'active' : 'inactive'}">
              {row.isActive ? '启用' : '停用'}
            </span>
          </td>
          <td>{row.fabricKgMax}</td>
          <td class="row-actions">
            {#if $isSupervisor}
              {#if row.isActive}
                <button class="btn ghost small" type="button" on:click={() => setActive(row.id, false)}
                  >停用</button
                >
              {:else}
                <button class="btn ghost small" type="button" on:click={() => setActive(row.id, true)}
                  >启用</button
                >
              {/if}
              <button class="btn ghost small" type="button" on:click={() => startEdit(row)}>编辑</button>
              <button class="btn danger small" type="button" on:click={() => remove(row.id)}>删除</button>
            {/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .check-label {
    flex-direction: row;
    align-items: center;
    gap: 0.45rem;
  }

  .check-label input {
    width: auto;
  }
</style>
