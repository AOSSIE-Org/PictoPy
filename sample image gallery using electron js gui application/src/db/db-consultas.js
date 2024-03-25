const { connection } = require('./conexion.js');

async function listar(){
  return (await connection).query(`SELECT * FROM imggallery ORDER BY imgCreationDate DESC;`);
};

async function crear(newGalleryItem){
  return (await connection).query(`INSERT INTO imggallery SET ?`, [newGalleryItem]);
};

async function editar(editGalleryItem, idImg){
  (await connection).query(`UPDATE imggallery SET ? WHERE idImg = ?;`, [editGalleryItem, idImg], function (error, results, fields) {
    if (error) throw error;
    console.log('updated ' + results.affectedRows + ' rows');
  });
};

async function eliminar(idImg) {
  (await connection).query(`DELETE FROM imggallery WHERE idImg = ?;`, [idImg], function (error, results, fields) {
    if (error) throw error;
    console.log('deleted ' + results.affectedRows + ' rows');
  });
};

module.exports = {listar, crear, editar, eliminar};
