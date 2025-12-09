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
  CircularProgress,
  Alert
} from "@mui/material";

function App() {
  const [catalogName, setCatalogName] = useState("");
  const [schemaName, setSchemaName] = useState("");
  const [tableName, setTableName] = useState("");

  const [columnOptions, setColumnOptions] = useState([]);
  const [selectedColumns, setSelectedColumns] = useState([]);

  const [dqRules, setDqRules] = useState([]);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  // Available DQ rules
  const dqRuleOptions = [
    { label: "Null Check", value: "Null Check" },
    { label: "Numeric Check", value: "Numeric Check" },
    { label: "Range Check", value: "Range Check" },
    { label: "Duplicate Check", value: "Duplicate Check" },
    { label: "Reference Check", value: "Reference Check" },
  ];

  // ---------------------------
  // FETCH COLUMNS FROM BACKEND
  // ---------------------------
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

  // ---------------------------
  // SUBMIT: RUN DQ RULES
  // ---------------------------
  const handleRunDQ = async () => {
    setLoading(true);
    setMessage("");

    const payload = {
      databaseType: catalogName,
      schemaName,
      tableName,
      columnName: selectedColumns,
      dqRule: dqRules,
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/dq-rule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      setMessage(`DQ Run Triggered Successfully! Run ID = ${data.run_id}`);
    } catch (error) {
      console.error(error);
      setMessage("❌ Error triggering DQ run");
    }

    setLoading(false);
  };

  // ---------------------------
  // REPROCESS LAST RUN
  // ---------------------------
  const handleReprocess = async () => {
    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(`http://127.0.0.1:8000/reprocess-last`, {
        method: "POST",
      });

      const data = await response.json();
      setMessage(`♻ Reprocess Triggered! New Run ID = ${data.run_id}`);
    } catch (error) {
      setMessage("❌ Reprocess Failed");
      console.error(error);
    }

    setLoading(false);
  };

  return (
    <Box
      sx={{
        maxWidth: 600,
        margin: "auto",
        mt: 5,
        p: 3,
        border: "1px solid #ddd",
        borderRadius: 2,
      }}
    >
      <Typography variant="h5" sx={{ textAlign: "center", mb: 3 }}>
        Data Quality Execution Form
      </Typography>

      {/* Display message */}
      {message && (
        <Alert severity={message.startsWith("❌") ? "error" : "success"} sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}

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

      {/* Column Multi-select */}
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

      {/* DQ Rules */}
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

      {/* Buttons */}
      <Button
        fullWidth
        variant="contained"
        color="primary"
        sx={{ mb: 2 }}
        onClick={handleRunDQ}
        disabled={loading}
      >
        {loading ? <CircularProgress size={24} /> : "Run DQ Rules"}
      </Button>

      <Button
        fullWidth
        variant="outlined"
        color="secondary"
        onClick={handleReprocess}
        disabled={loading}
      >
        {loading ? <CircularProgress size={24} /> : "Reprocess Last Run"}
      </Button>
    </Box>
  );
}

export default App;
