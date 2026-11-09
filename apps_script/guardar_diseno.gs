/** Guardado de Diseño3D: TAG numéricos, actualización, deduplicación y renombrado.
 * Actualizar la implementación existente para conservar su URL /exec.
 */
const DESIGN_SHEET_ID = '1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4';
const DESIGN_TAB = 'Diseño3D';
const DESIGN_BACKUP_TAB = 'Respaldo_Diseño3D';

function normalizeDesignTag(value) {
  return String(value == null ? '' : value).trim().normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').toUpperCase().replace(/\s+/g, ' ');
}
function designResponse(value) {
  return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON);
}
function doPost(e) {
  const lock = LockService.getScriptLock();
  let locked = false;
  try {
    const request = JSON.parse(e.postData.contents);
    const tag = String(request.tag == null ? '' : request.tag).trim();
    const original = String(request.original_tag == null ? '' : request.original_tag).trim();
    const raw = typeof request.datos === 'string' ? request.datos : JSON.stringify(request.datos);
    if (!tag || !raw || raw.length > 50000) throw new Error('TAG o tamaño del diseño inválido.');
    const data = JSON.parse(raw);
    if (!data || !Array.isArray(data.nozzles)) throw new Error('El diseño necesita una lista de boquillas.');
    locked = lock.tryLock(30000);
    if (!locked) throw new Error('Otro guardado está en curso. Reintenta; tu borrador no se ha modificado.');
    const book = SpreadsheetApp.openById(DESIGN_SHEET_ID);
    const sheet = book.getSheetByName(DESIGN_TAB);
    if (!sheet) throw new Error('No existe la hoja ' + DESIGN_TAB);
    const rows = sheet.getDataRange().getValues();
    const key = normalizeDesignTag(tag), oldKey = normalizeDesignTag(original);
    const targets = [], sources = [];
    for (let i = 1; i < rows.length; i++) {
      const rowKey = normalizeDesignTag(rows[i][0]); // Convierte también los TAG numéricos a texto.
      if (rowKey === key) targets.push(i + 1);
      if (oldKey && oldKey !== key && rowKey === oldKey) sources.push(i + 1);
    }
    const affected = [...new Set(targets.concat(sources))];
    // Resguardar todas las versiones anteriores ANTES de sobreescribir o borrar.
    if (affected.length) {
      let backup = book.getSheetByName(DESIGN_BACKUP_TAB);
      if (!backup) {
        backup = book.insertSheet(DESIGN_BACKUP_TAB);
        backup.appendRow(['Fecha UTC', 'TAG anterior', 'Datos JSON', 'TAG destino', 'Fila original']);
      }
      const snapshot = affected.map(row => [new Date().toISOString(), String(rows[row - 1][0]), String(rows[row - 1][1]), tag, row]);
      backup.getRange(backup.getLastRow() + 1, 1, snapshot.length, 5).setValues(snapshot);
      SpreadsheetApp.flush();
    }
    const targetRow = targets.length ? targets[0] : sheet.getLastRow() + 1;
    const range = sheet.getRange(targetRow, 1, 1, 2);
    range.setNumberFormat('@');
    range.setValues([[tag, raw]]);
    SpreadsheetApp.flush();
    const written = range.getValues()[0];
    if (String(written[0]).trim() !== tag || String(written[1]) !== raw) {
      throw new Error('No se pudo verificar el TAG nuevo; no se eliminó el TAG anterior.');
    }
    // El nuevo registro ya está verificado: retirar originales y duplicados.
    const remove = affected.filter(row => row !== targetRow).sort((a, b) => b - a);
    remove.forEach(row => sheet.deleteRow(row));
    SpreadsheetApp.flush();
    const finalRow = targetRow - remove.filter(row => row < targetRow).length;
    const finalData = sheet.getRange(finalRow, 1, 1, 2).getValues()[0];
    if (String(finalData[0]).trim() !== tag || String(finalData[1]) !== raw) {
      throw new Error('Revisa el resultado y la hoja de respaldo antes de continuar.');
    }
    return designResponse({ok: true, tag, renamed_from: sources.length ? original : null, removed_rows: remove.length});
  } catch (error) {
    return designResponse({ok: false, error: String(error.message || error)});
  } finally {
    if (locked) lock.releaseLock();
  }
}
function doGet() {
  return designResponse({ok: true, service: 'Diseño3D', supports_rename: true});
}
