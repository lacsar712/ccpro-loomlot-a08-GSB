<script>
  import { onMount } from 'svelte';
  import { api, VAT_STATUS, toLocalInput, fromLocalInput } from '../lib/api.js';

  let vats = [];
  let rows = [];
  let versions = [];
  let error = '';
  let staleRecipe = '';
  let form = {
    vatId: '',
    recipeVersionId: '',
    fabricKg: 20,
    startedAt: toLocalInput(new Date().toISOString()),
    operatorName: '染程操作员',
  };
  let editing = null;

  $: houseId = (() => {
    const v = vats.find((x) => String(x.id) === String(form.vatId));
    return v ? v.dyeHouseId : null;
  })();

  // 配方下拉只列所选染缸所属染坊的启用版本——与后端命中规则同源
  $: recipeOptions = versions.filter(
    (ver) => ver.isActive && ver.dyeHouseId === houseId
  );

  $: versionValid = recipeOptions.some(
    (ver) => String(ver.id) === String(form.recipeVersionId)
  );

  $: selectedVersion = versionValid
    ? recipeOptions.find((ver) => String(ver.id) === String(form.recipeVersionId))
    : null;

  function pickVat(vatId) {
    form.vatId = vatId;
    const v = vats.find((x) => String(x.id) === String(vatId));
    const first = versions.find(
      (ver) => ver.isActive && v && ver.dyeHouseId === v.dyeHouseId
    );
    form.recipeVersionId = first ? String(first.id) : '';
    staleRecipe = '';
  }

  function pickRecipe(versionId) {
    form.recipeVersionId = versionId;
  }

  async function load() {
    error = '';
    try {
      [vats, rows, versions] = await Promise.all([
        api('/vats'),
        api('/dye-lots'),
        api('/recipe-versions'),
      ]);
      const usable = vats.filter((v) => v.status === 'ready' || v.status === 'dyeing');
      if (!form.vatId && usable.length) form.vatId = String(usable[0].id);
      else if (!form.vatId && vats.length) form.vatId = String(vats[0].id);
      if (!form.recipeVersionId && recipeOptions.length) {
        form.recipeVersionId = String(recipeOptions[0].id);
      }
    } catch (e) {
      error = e.message;
    }
  }

  onMount(load);

  function vatLabel(id) {
    const v = vats.find((x) => x.id === id);
    if (!v) return id;
    return `${v.vatCode}（${VAT_STATUS[v.status] || v.status}）`;
  }

  async function save() {
    error = '';
    if (!form.recipeVersionId || !selectedVersion) {
      error = '请选择该染坊的启用配方';
      return;
    }
    try {
      const body = {
        vatId: Number(form.vatId),
        recipeName: selectedVersion.recipeName,
        fabricKg: Number(form.fabricKg),
        startedAt: fromLocalInput(form.startedAt),
        operatorName: form.operatorName.trim(),
      };
      if (editing) {
        await api(`/dye-lots/${editing}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await api('/dye-lots', { method: 'POST', body: JSON.stringify(body) });
      }
      editing = null;
      staleRecipe = '';
      form = {
        ...form,
        recipeVersionId: recipeOptions.length ? String(recipeOptions[0].id) : '',
        fabricKg: 20,
        startedAt: toLocalInput(new Date().toISOString()),
      };
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  function startEdit(row) {
    editing = row.id;
    const matched = versions.find(
      (ver) =>
        ver.isActive &&
        ver.recipeName === row.recipeName &&
        (() => {
          const v = vats.find((x) => x.id === row.vatId);
          return v && ver.dyeHouseId === v.dyeHouseId;
        })()
    );
    staleRecipe = matched ? '' : row.recipeName;
    form = {
      vatId: String(row.vatId),
      recipeVersionId: matched ? String(matched.id) : '',
      fabricKg: row.fabricKg,
      startedAt: toLocalInput(row.startedAt),
      operatorName: row.operatorName,
    };
  }

  async function remove(id) {
    if (!confirm('确认删除该染程？')) return;
    error = '';
    try {
      await api(`/dye-lots/${id}`, { method: 'DELETE' });
      await load();
    } catch (e) {
      error = e.message;
    }
  }
</script>

<h1 class="page-title">染程</h1>
<p class="page-sub">
  仅 ready / dyeing 染缸可开缸；配方必须命中染缸所属染坊的启用版本，布重不得超过该版本上限。
</p>

<div class="panel" style="margin-bottom:1rem;">
  <div class="form-grid">
    <label
      >染缸
      <select value={form.vatId} on:change={(e) => pickVat(e.currentTarget.value)}>
        {#each vats as v}
          <option value={String(v.id)}
            >{v.vatCode} · {VAT_STATUS[v.status] || v.status} · {v.fiberType}</option
          >
        {/each}
      </select>
    </label>
    <label>
      配方
      <select value={form.recipeVersionId} on:change={(e) => pickRecipe(e.currentTarget.value)}>
        {#if !form.recipeVersionId}
          <option value="" disabled>
            {staleRecipe ? `${staleRecipe}（版本已停用，请改选启用配方）` : '请选择启用配方'}
          </option>
        {/if}
        {#each recipeOptions as ver}
          <option value={String(ver.id)}>
            {ver.recipeName} v{ver.versionNo} · 上限 {ver.fabricKgMax}kg
          </option>
        {/each}
      </select>
    </label>
    <label
      >布料 kg
      <input type="number" step="0.1" bind:value={form.fabricKg} />
      {#if selectedVersion}
        <small class="hint">当前版本单次上限 {selectedVersion.fabricKgMax}kg</small>
      {/if}
    </label>
    <label>开始时间 <input type="datetime-local" bind:value={form.startedAt} /></label>
    <label>操作员 <input bind:value={form.operatorName} /></label>
  </div>
  <div class="toolbar">
    <button class="btn" type="button" on:click={save}>{editing ? '保存修改' : '新建染程'}</button>
    {#if editing}
      <button
        class="btn ghost"
        type="button"
        on:click={() => {
          editing = null;
          staleRecipe = '';
        }}>取消</button
      >
    {/if}
  </div>
  {#if error}<p class="err">{error}</p>{/if}
</div>

<div class="panel">
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>染缸</th>
        <th>配方</th>
        <th>布料 kg</th>
        <th>开始</th>
        <th>操作员</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        <tr>
          <td>{row.id}</td>
          <td>{vatLabel(row.vatId)}</td>
          <td>{row.recipeName}</td>
          <td>{row.fabricKg}</td>
          <td>{new Date(row.startedAt).toLocaleString()}</td>
          <td>{row.operatorName}</td>
          <td class="row-actions">
            <button class="btn ghost small" type="button" on:click={() => startEdit(row)}>编辑</button>
            <button class="btn danger small" type="button" on:click={() => remove(row.id)}>删除</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .hint {
    color: var(--indigo-mist);
    font-size: 0.72rem;
    margin-top: 0.25rem;
  }
</style>
