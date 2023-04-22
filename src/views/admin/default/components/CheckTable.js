import {
  Flex,
  Table,
  Checkbox,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  useColorModeValue,
} from "@chakra-ui/react";
import React, { useMemo, useState, useEffect } from "react";

import "assets/css/App.css";
import {
  useGlobalFilter,
  usePagination,
  useSortBy,
  useTable,
} from "react-table";

// Custom components
import Card from "components/card/Card";
import Menu from "components/menu/MainMenu";

let USDollar = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
});

export default function CheckTable(props) {
  // console.log("table props", props);
  // const [ columnsData, setColumnsData ] = useState(props.columnsData);
  // const [ tableData, setTableData ] = useState(props.tableData);
  const { columnsData, tableData } = props;

  const columns = useMemo(() => columnsData, [columnsData]);
  const data = useMemo(() => tableData, [tableData]);

  // useEffect(() => {
  //   console.log("Changed Table", props);
  //   setColumnsData(props.columnsData);
  //   setTableData(props.tableData);
  // },[props]);

  const tableInstance = useTable(
    {
      columns,
      data,
    },
    useGlobalFilter,
    useSortBy,
    usePagination
  );

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    page,
    prepareRow,
    initialState,
  } = tableInstance;
  initialState.pageSize = 11;

  const textColor = useColorModeValue("#secondaryGray.900", "white");

  const borderColor = useColorModeValue("gray.200", "whiteAlpha.100");
  return (
    <Card
      direction='column'
      w='100%'
      px='0px'
      overflowX={{ sm: "scroll", lg: "hidden" }}>
      <Flex px='25px' justify='space-between' align='center'>
        <Text
          color={textColor}
          fontSize='22px'
          fontWeight='700'
          lineHeight='100%'>
          Positions
        </Text>
        <Menu />
      </Flex>
      <Table {...getTableProps()} variant='simple' color='gray.500' mb='24px'>
        <Thead>
          {headerGroups.map((headerGroup, index) => (
            <Tr {...headerGroup.getHeaderGroupProps()} key={index}>
              {headerGroup.headers.map((column, index) => (
  <Th
  {...column.getHeaderProps(column.getSortByToggleProps())}
  pe='10px'
  key={index}
  borderColor={borderColor}>
  <Flex
    justify='space-between'
    align='center'
    fontSize={{ sm: "10px", lg: "12px" }}
    color='gray.400'>
    {column.render("Header")}
    {column.isSorted ? (
      <span
        className={`table-header-sort-icon ${
          column.isSortedDesc ? 'desc' : 'asc'
        }`}
        aria-hidden='true'
      ></span>
    ) : null}
  </Flex>
</Th>

))}

            </Tr>
          ))}
        </Thead>
        <Tbody {...getTableBodyProps()}>
          {page.map((row, index) => {
            prepareRow(row);
            return (
              <Tr {...row.getRowProps()} key={index}>
                {row.cells.map((cell, index) => {
                  let data = "";
                  if (cell.column.Header === "ASSET") {
                    data = (
                      <Flex align='center'>
                        {/* <Checkbox
                          defaultChecked={cell.value[1]}
                          colorScheme='brandScheme'
                          me='10px'
                        /> */}
                        <Text color={textColor} fontSize='sm' fontWeight='700'>
                          {cell.value}
                        </Text>
                      </Flex>
                    );
                  } else if (cell.column.Header === "PRICE") {
                    data = (
                      <Flex align='center'>
                        <Text
                          me='10px'
                          color={textColor}
                          fontSize='sm'
                          fontWeight='700'>
                          {USDollar.format(cell.value)}
                        </Text>
                      </Flex>
                    );
                  } else if (cell.column.Header === "QUANTITY") {
                    data = (
                      <Text color={textColor} fontSize='sm' fontWeight='700'>
                        {cell.value}
                      </Text>
                    );
                  } else if (cell.column.Header === "MARKET VALUE") {
                    data = (
                      <Text color={textColor} fontSize='sm' fontWeight='700'>
                        {cell.value}
                      </Text>
                    );
                  } else if (cell.column.Header === "PROFIT LOSS") {
                    const textColor1= cell.value >= 0 ? "green.500" : "red.500";
                    data = (
                      <Text color={textColor1} fontSize='sm' fontWeight='700'>
                        {cell.value}
                      </Text>
                    );
                  }
                  return (
                    <Td
                      {...cell.getCellProps()}
                      key={index}
                      fontSize={{ sm: "14px" }}
                      minW={{ sm: "150px", md: "200px", lg: "auto" }}
                      borderColor='transparent'>
                      {data}
                    </Td>
                  );
                })}
              </Tr>
            );
          })}
        </Tbody>
      </Table>
    </Card>
  );
}
