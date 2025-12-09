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

function DQForm() {
  const [catalogName, setCatalogName] = useState("");
  const [schemaName, setSchemaName] = useState("");
  const [tableName, setTableName] = useState("");

  const [columnOptions, setColumnOptions] = useState([]);
  const [selectedColumns, setSelectedColumns] = useState([]);

  const [dqRules, setDqRules] = useState([]);

  // Available DQ rules
  const dqRuleOptions = [
    { label: "Null Check", value: "Null Check" },
    { label: "Numeric Check", value: "Numeric Check" },
    { label: "Range Check", value: "Range Check" },
    { label: "Duplicate Check", value: "Duplicate Check" },
    { label: "Reference Check", value: "Reference Check" },
  ];

  // 🔥 Fetch columns when catalog, schema, table changes
  useEffect(() => {
    if (!catalogName || !schemaName || !tableName) return;

    const fetchColumns = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:8000/columns?catalog=${catalogName}&schema=${schemaName}&table=${tableName}`
        );
        const data = await response.json();

        if (data.columns) {
          setColumnOptions(data.columns);
        } else {
          setColumnOptions([]);
        }
      } catch (error) {
        console.error("Error fetching columns:", error);
        setColumnOptions([]);
      }
    };

    fetchColumns();
  }, [catalogName, schemaName, tableName]);

  // Handle Submit
  const handleSubmit = async () => {
    const payload = {
      databaseType: catalogName,
      schemaName,
      tableName,
      columnName: selectedColumns,   // MULTIPLE columns sent
      dqRule: dqRules,               // RULE NAMES
    };

    console.log("Sending payload:", payload);

    try {
      const response = await fetch("http://127.0.0.1:8000/dq-rule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      console.log("API Response:", data);

      alert(`DQ Run Triggered! Run ID = ${data.run_id}`);
    } catch (err) {
      console.error(err);
      alert("Error triggering DQ run");
    }
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

      {/* Catalog Name */}
      <TextField
        fullWidth
        label="Catalog Name"
        value={catalogName}
        onChange={(e) => setCatalogName(e.target.value)}
        sx={{ mb: 2 }}
      />

      {/* Schema Name */}
      <TextField
        fullWidth
        label="Schema Name"
        value={schemaName}
        onChange={(e) => setSchemaName(e.target.value)}
        sx={{ mb: 2 }}
      />

      {/* Table Name */}
      <TextField
        fullWidth
        label="Table Name"
        value={tableName}
        onChange={(e) => setTableName(e.target.value)}
        sx={{ mb: 2 }}
      />

      {/* Dynamic Column Dropdown (Multi-Select) */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Select Columns</InputLabel>
        <Select
          multiple
          value={selectedColumns}
          onChange={(e) => setSelectedColumns(e.target.value)}
          renderValue={(selected) => selected.join(", ")}
        >
          {columnOptions.length === 0 ? (
            <MenuItem disabled>No columns available</MenuItem>
          ) : (
            columnOptions.map((col) => (
              <MenuItem key={col} value={col}>
                <Checkbox checked={selectedColumns.includes(col)} />
                <ListItemText primary={col} />
              </MenuItem>
            ))
          )}
        </Select>
      </FormControl>

      {/* DQ Rules Multi-select */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Select DQ Rules</InputLabel>
        <Select
          multiple
          value={dqRules}
          onChange={(e) => setDqRules(e.target.value)}
          renderValue={(selected) => selected.join(", ")}
        >
          {dqRuleOptions.map((rule) => (
            <MenuItem key={rule.value} value={rule.value}>
              <Checkbox checked={dqRules.includes(rule.value)} />
              <ListItemText primary={rule.label} />
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Submit Button */}
      <Button fullWidth variant="contained" onClick={handleSubmit}>
        Run DQ Rules
      </Button>
    </Box>
  );
}

export default DQForm;
