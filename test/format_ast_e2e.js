#!/usr/bin/env node
'use strict';

const fs = require('fs');
const { formatLangAst } = require('../web/program_host.js');

if (process.argv.length !== 3) {
  console.error('usage: format_ast_e2e.js input.ast');
  process.exit(2);
}

process.stdout.write(`${formatLangAst(fs.readFileSync(process.argv[2], 'utf8'))}\n`);
