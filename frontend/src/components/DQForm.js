import React, { useState, useEffect } from "react";
import {
  Box,
  TextField,
  Select,
  MenuItem,
  Button,
  Typography,
  FormControl,
  InputLabel,
  Checkbox,
  ListItemText,
} from "@mui/material";

function DQForm({ onRunDQ, onReprocess, loading, message }) {
  const [catalogName, setCatalogName] = useState("");
  const [schemaName, setSchemaName] = useState("");
  const [tableName, setTableName] = useState("");

  const [columnOptions, setColumnOptions] = useState([]);
  const [selectedColumns, setSelectedColumns] = useState([]);

  const [dqRules, setDqRules] = useState([]);

  const dqRuleOptions = [
    { label: "Null Check", value: "NULL_CHECK" },
    { label: "Numeric Check", value: "NUMERIC_CHECK" },
    { label: "Range Check", value: "RANGE_CHECK" },
    { label: "Duplicate Check", value: "DUPLICATE_CHECK" },
    { label: "Reference Check", value: "REFERENCE_CHECK" },
  ];

  // Fetch columns from backend
  useEffect(() => {
    if (!catalogName || !schemaName || !tableName) return;

    const fetchColumns = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:8000/columns?catalog=${catalogName}&schema=${schemaName}&table=${tableName}`
        );

        const data = await response.json();
        setColumnOptions(data.columns || []);
      } catch (error) {
        console.error("Column fetch error:", error);
        setColumnOptions([]);
      }
    };

    fetchColumns();
  }, [catalogName, schemaName, tableName]);

  // Submit data to App.js handler
  const submitForm = () => {
    const payload = {
      databaseType: catalogName,
      schemaName,
      tableName,
      columnName: selectedColumns,
      dqRule: dqRules,
    };

    onRunDQ(payload);
  };

  // Reprocess last run for same config_id (schema+table)
  const handleReprocessClick = () => {
    const config_id = `${schemaName}_${tableName}`;
    onReprocess(config_id);
  };

  return (
    <Box
      sx={{
        maxWidth: 600,
        margin: "auto",
        mt: 5,
        p: 3,
        border: "1px solid #ccc",
        borderRadius: 2,
      }}
    >
      <Typography variant="h5" sx={{ textAlign: "center", mb: 3 }}>
        Data Quality Execution Form
      </Typography>

      {message && (
        <Typography sx={{ mb: 2, color: "green", textAlign: "center" }}>
          {message}
        </Typography>
      )}

      {/* Catalog */}
      <TextField
        fullWidth
        label="Catalog Name"
        value={catalogName}
        onChange={(e) => setCatalogName(e.target.value)}
        sx={{ mb: 2 }}
      />

      {/* Schema */}
      <TextField
        fullWidth
        label="Schema Name"
        value={schemaName}
        onChange={(e) => setSchemaName(e.target.value)}
        sx={{ mb: 2 }}
      />

      {/* Table */}
      <TextField
        fullWidth
        label="Table Name"
        value={tableName}
        onChange={(e) => setTableName(e.target.value)}
        sx={{ mb: 2 }}
      />

      {/* Column Multi Select */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Select Columns</InputLabel>
        <Select
          multiple
          value={selectedColumns}
          onChange={(e) => setSelectedColumns(e.target.value)}
          renderValue={(sel) => sel.join(", ")}
        >
          {columnOptions.map((col) => (
            <MenuItem key={col} value={col}>
              <Checkbox checked={selectedColumns.includes(col)} />
              <ListItemText primary={col} />
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* DQ Rules */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Select DQ Rules</InputLabel>
        <Select
          multiple
          value={dqRules}
          onChange={(e) => setDqRules(e.target.value)}
          renderValue={(sel) => sel.join(", ")}
        >
          {dqRuleOptions.map((rule) => (
            <MenuItem key={rule.value} value={rule.value}>
              <Checkbox checked={dqRules.includes(rule.value)} />
              <ListItemText primary={rule.label} />
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Execute DQ Button */}
      <Button
        fullWidth
        variant="contained"
        onClick={submitForm}
        disabled={loading}
        sx={{ mb: 2 }}
      >
        {loading ? "Running..." : "Run DQ Rules"}
      </Button>

      {/* Reprocess Button */}
      <Button
        fullWidth
        variant="outlined"
        color="secondary"
        disabled={!schemaName || !tableName || loading}
        onClick={handleReprocessClick}
      >
        {loading ? "Reprocessing..." : "Reprocess Last Execution"}
      </Button>
    </Box>
  );
}

export default DQForm;
